Simple algorithm to trade a single stock based upon certain rules.
The data is defined in the pipeline definition.
The selection logic is performed in the code.
'''
 
# The following imports need to included when using Pipeline
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline, CustomFactor
 
# Import all the built in Quantopian filters and factors (just in case)
import quantopian.pipeline.filters as Filters
import quantopian.pipeline.factors as Factors
 
# Import Pandas and Numpy (just in case we want to use their functionality)
import pandas as pd
import numpy as np
 
# Import any specialiazed packages here (eg scipy.optimize or scipy.stats)
pass
 
# Import any needed datasets
from quantopian.pipeline.data.builtin import USEquityPricing
 
 
# Set any 'constants' you will be using
MY_STOCKS = symbols('AAPL', 'WFC', 'MSFT', 'AMZN', 'FB', 'XOM', 'C', 'UNH', 'DIS', 'PM',
                   'T', 'KO', 'VZ', 'GE', 'WMT', 'BAC', 'PG', 'CVX', 'V', 'PFE')
 
# Let's equally weight our 'potential' positions
# Note that this may not make the best use of cash because we will
# not be investing a positions 'share' when it doesn't pass the rules
WEIGHT = 1.0 / len(MY_STOCKS)
 
def initialize(context):
    """
    Called once at the start of the algorithm.
    """   
    
    # Set commission model or omit and the default Q models will be used
    # set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    # set_slippage(slippage.FixedSlippage(spread=0))
    
    # Attach the pipeline defined in my_pipe so we have data to use
    attach_pipeline(pipe_definition(context), name='my_data')
  
    # Schedule when to trade.
    schedule_function(trade, date_rules.every_day(), time_rules.market_open())
 
    # Schedule when to record any tracking data
    schedule_function(record_vars, date_rules.every_day(), time_rules.market_close())
 
         
def pipe_definition(context):
    '''
    Here is where the pipline definition is set.
    Specifically it defines which collumns appear in the resulting dataframe.
    Think of its defining a big spreadsheet (really a dataframe) of data.
    Don't think of the pipeline as doing any logic. That's later in the algo.
    '''
    
    # Create a universe filter which defines our baseline set of securities
    # If no filter is used then ALL assets in the Q database will potentially be returned
    # This is not what one typically wants because 
    #    1) it includes a mix of ETFs and stocks
    #    2) it includes very low liquid and 'penny' stocks
    #
    # This filter can also be used as a mask in factors to potentially speed up some calcs
    # Just want a single stock though so use the StaticAssets filter
    universe = Filters.StaticAssets(MY_STOCKS)
    
    # Create any basic data factors that your logic will use.
    # This is done by simply using the 'latest' method on a datacolumn object.
    # Just ensure the dataset is imported first.
    close_price = USEquityPricing.close.latest
 
    # Create any built in factors you want to use (in this case Returns). 
    # Just ensure they are imported first.
    sma_15 = Factors.SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=15, mask=universe)   
    
    # Create any custom factors you want to use 
    # Just ensure they are defined somewhere in the code.
    pass
    
    # Create any built in filters you want to use.
    pass
 
    # Create any filters based upon factors defined above.
    # These are easily made with the built in methods such as '.top' etc applied to a factor
    pass
 
    # Define the columns and any screen which we want our pipeline to return
    # This becomes the data that our algorithm will use to make trading decisions
    return Pipeline(
            columns = {
            'close_price' : close_price,
            'sma_15' : sma_15,
            },
            screen = universe,
            )
    
 
def before_trading_start(context, data):
    '''
    Run pipeline_output to get the latest data for each security.
    The data is returned in a 2D pandas dataframe. Rows are the security objects.
    Columns are what was defined in the pipeline definition.
    '''
    
    # Get a dataframe of our pipe data. Placed in the context object so it's available
    # to other functions and methods (quasi global)
    context.output = pipeline_output('my_data')
       
   
def trade(context, data):
    '''
    This is a scheduled function to execute all buys and sells
    '''
    # Note that no logic was done in the pipeline. Just fetched the data.
    # Here is where you can filter, sort, and do whatever you want with that data.
    # Anything that could have been done in pipeline can be done with the
    # dataframe that it returns. Use the pandas methods on context.output.
    
 
    
    open_rules = 'close_price > sma_15'
    open_these = context.output.query(open_rules).index.tolist()
 
    for stock in open_these:
        if stock not in context.portfolio.positions and data.can_trade(stock):
            order_target_percent(stock, WEIGHT)
    
    
    close_rules = 'close_price < sma_15'
    close_these = context.output.query(close_rules).index.tolist()
 
    for stock in close_these:
        if stock in context.portfolio.positions and data.can_trade(stock):
            order_target_percent(stock, 0)
 
                  
 
def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    
    # Record the number of positions held each day
    record(leverage=context.account.leverage,
           positions=len(context.portfolio.positions))