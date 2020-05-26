from quantopian.pipeline import Pipeline
from quantopian.pipeline.data import EquityPricing
from quantopian.pipeline.data.factset import Fundamentals, EquityMetadata
from quantopian.pipeline.domain import US_EQUITIES
from quantopian.pipeline.factors import SimpleMovingAverage

is_share = EquityMetadata.security_type.latest.eq('SHARE')
is_primary = EquityMetadata.is_primary.latest
primary_shares = (is_share & is_primary)
market_cap = Fundamentals.mkt_val.latest

universe = market_cap.top(1000, mask=primary_shares)

# 1-month moving average factor.
fast_ma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=21)

# 6-month moving average factor.
slow_ma = SimpleMovingAverage(inputs=[EquityPricing.close], window_length=126)

# Divide fast_ma by slow_ma to get momentum factor and z-score.
momentum = fast_ma / slow_ma
momentum_factor = momentum.zscore()


# Create a US equities pipeline with our momentum factor, screening down to our universe.
pipe = Pipeline(
    columns={
        'momentum_factor': momentum_factor,
    },
    screen=universe,
    domain=US_EQUITIES,
)

# Run the pipeline from 2016 to 2019 and display the first few rows of output.
from quantopian.research import run_pipeline
factor_data = run_pipeline(pipe, '2016-01-01', '2019-01-01')
print("Result contains {} rows of output.".format(len(factor_data)))
factor_data.head()