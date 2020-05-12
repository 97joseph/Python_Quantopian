# This is the zipline script that I use to verify the performances  
# of the pairs suggested by pairslog.com (note: obviuosly  
# the results published by pairslog.com are correct and do not  
# need verification, but I like to be sure that I can reproduce  
# exactly the conditions under which the measurements were made)  
# Pairs trading is therefore performed according to the following  
# pairslog.com rules:  
# - the spread is simply the ratio between the prices of the stocks  
# - the zscore is what pairslog calls delta  
# - the window_lenght is set to 14 days  
# - the slippage is set to 0  
# - the commissions are set to 0  
# - the spread is bought when zscore (i.e.delta, in pairslog language) is <= -2  
#   and sold when zscore is >= 2. The position is closed when zscore reverts to 0.  
#  
import matplotlib.pyplot as plt  
import numpy as np  
import pandas as pd  
import statsmodels.api as sm  
from datetime import datetime  
import pytz  
from logbook import Logger

from zipline.algorithm import TradingAlgorithm  
from zipline.transforms import batch_transform  
from zipline.utils.factory import load_from_yahoo  
from zipline.finance import commission,slippage

class Pairtrade(TradingAlgorithm):  
    def initialize(self,stockA,stockB, window_length=14):  
        self.spreads = []  
        self.capital_base=10000  
        self.invested = 0  
        self.window_length = window_length  
        self.instant_fill=True                    #Pairslog results are built using EOD data. (I assumed same day of signal)  
        self.stockA=stockA  
        self.stockB=stockB  
        self.posSizeA=self.capital_base  
        self.posSizeB=self.capital_base           #I assumed 50% margin for both long and short trades  
        self.set_commission(commission.PerTrade(cost=0))        #Pairslog results do not consider commissions.  
        self.set_slippage(slippage.FixedSlippage(spread=0.0))   #Pairslog results are built using EOD data and do not consider liquidity factor.  
        self.txnumber=0  
        self.trades = pd.DataFrame()

    def handle_data(self, data):  
        zscore = self.compute_zscore(data)  
        if (len(self.spreads) < self.window_length):  
            return  
        self.record(zscores=zscore)  
        self.place_orders(data, zscore)

    def compute_zscore(self, data):  
        spread = data[self.stockA].price / data[self.stockB].price  
        self.spreads.append(spread)  
        spread_wind = self.spreads[-self.window_length:]  
        zscore = (spread - np.mean(spread_wind)) / np.std(spread_wind)  
        return zscore

    def place_orders(self, data, zscore):  
        """Buy spread if zscore is <= -2, sell if zscore >= 2,  
           close the trade when zscore crosses 0  
        """  
        #log.info(str(self.get_datetime())+' amount: '+str(self.portfolio.positions[self.stockA].amount))  
        if zscore >= 2.0 and self.invested==0:  
            self.order(self.stockA, -int(self.posSizeA/ data[self.stockA].price))  
            self.order(self.stockB, int(self.posSizeB / data[self.stockB].price))  
            self.invested = 1  
            #log.info(str(self.get_datetime())+' amountS: '+str(self.portfolio.positions[self.stockA].amount))  
        elif zscore <= -2.0 and self.invested==0:  
            self.order(self.stockA, int(self.posSizeA/ data[self.stockA].price))  
            self.order(self.stockB, -int(self.posSizeB / data[self.stockB].price))  
            self.invested = 2  
            #log.info(str(self.get_datetime())+' amountB: '+str(self.portfolio.positions[self.stockA].amount))  
        elif (zscore <= 0 and self.invested==1) or (zscore >= 0 and self.invested==2):  
            self.sell_spread()  
            self.invested = 0  


    def sell_spread(self):  
        """  
        decrease exposure, regardless of posstockB_amountition long/short.  
        buy for a short position, sell for a long.  
        """  
        self.txnumber=self.txnumber+1  
        stockB_amount = self.portfolio.positions[self.stockB].amount  
        self.order(self.stockB, -1 * stockB_amount)  
        #log.info(str(self.get_datetime())+' '+str(stockB_amount))  
        stockA_amount = self.portfolio.positions[self.stockA].amount  
        self.order(self.stockA, -1 * stockA_amount)

if __name__ == '__main__':  
    log = Logger('')  
    start = datetime(2011, 3, 28, 0, 0, 0, 0, pytz.utc)  
    end = datetime(2014, 3, 28, 0, 0, 0, 0, pytz.utc)  
    #stockA='gaz'  
    #stockB='uco'  
    #stockA='mzz'  
    #stockB='xop'  
    stockA='IVV'  
    stockB='SPY'  
    data = load_from_yahoo(stocks=[stockA, stockB], indexes={},  
                           start=start, end=end)  
    pairtrade = Pairtrade(stockA,stockB)  
    results = pairtrade.run(data)  
    #data['spreads'] = np.nan

    ax1 = plt.subplot(411)  
    data[[stockA,stockB]].plot(ax=ax1)  
    plt.ylabel('price')  
    plt.setp(ax1.get_xticklabels(), visible=False)

    ax2 = plt.subplot(412, sharex=ax1)  
    results.zscores.plot(ax=ax2, color='r')  
    plt.ylabel('zscore')  
    ax3 = plt.subplot(413, sharex=ax1)  
    pd.TimeSeries(np.array(pairtrade.spreads),results.zscores.index).plot(ax=ax3, color='b')  
    plt.ylabel('spread')  
    ax4 = plt.subplot(414, sharex=ax1)  
    results['portfolio_value'].plot(ax=ax4, color='b')  
    plt.ylabel('portfolio value')

    plt.gcf().set_size_inches(18, 8)  
    plt.show()  
    print(results['portfolio_value'])  
    print('Number of trades:'+str(pairtrade.txnumber))  