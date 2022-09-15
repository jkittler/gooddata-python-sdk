# (C) 2022 GoodData Corporation
from pathlib import Path
from typing import Tuple

from tests_support.vcrpy_utils import get_vcr

from gooddata_pandas import DataFrameFactory
from gooddata_sdk import Attribute, ExecutionDefinition, ObjId, SimpleMetric, TotalDefinition, TotalDimension
from gooddata_sdk.compute.model.execution import ResultSizeDimensionsLimitsExceeded

gd_vcr = get_vcr()

_current_dir = Path(__file__).parent.absolute()
_fixtures_dir = _current_dir / "fixtures"


def _run_and_validate_results(gdf: DataFrameFactory, exec_def: ExecutionDefinition, expected: Tuple[int, int]) -> str:
    # generate dataframe from exec_def
    result, response = gdf.for_exec_def(exec_def=exec_def)
    assert result.values.shape == expected

    # use result ID from computation above and generate dataframe just from it
    result_from_result_id = gdf.for_exec_result_id(response.result_id)
    assert result_from_result_id.values.shape == expected

    # compare dataframes generated using both methods above
    assert result.to_string() == result_from_result_id.to_string()

    return response.result_id


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_two_dim1.yaml"))
def test_dataframe_for_exec_def_two_dim1(gdf: DataFrameFactory):
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[["state", "region"], ["product_category", "measureGroup"]],
    )
    exec_result_id = _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(48, 8))

    # check also label overrides
    overrides = {
        "labels": {
            "state": {"title": "STATE LABEL"},
        },
        "metrics": {
            "price": {"title": "PRICE LABEL"},
        },
    }
    result = gdf.for_exec_result_id(exec_result_id, label_overrides=overrides)
    assert result.to_string().find(overrides["labels"]["state"]["title"]) == 262
    assert result.to_string().find(overrides["metrics"]["price"]["title"]) == 162


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_two_dim1.yaml"))
def test_dataframe_for_exec_def_dimensions_limits_failure(gdf: DataFrameFactory):
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[["state", "region"], ["product_category", "measureGroup"]],
    )

    result_size_dimensions_limits = (1, 1)
    exception = None
    try:
        gdf.for_exec_def(exec_def=exec_def, result_size_dimensions_limits=result_size_dimensions_limits)
    except ResultSizeDimensionsLimitsExceeded as e:
        exception = e

    assert type(exception) is ResultSizeDimensionsLimitsExceeded
    assert exception.result_size_dimensions_limits == result_size_dimensions_limits
    assert exception.first_violating_index == 0


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_two_dim2.yaml"))
def test_dataframe_for_exec_def_two_dim2(gdf: DataFrameFactory):
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[["region", "state", "product_category"], ["measureGroup"]],
    )
    _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(182, 2))


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_two_dim3.yaml"))
def test_dataframe_for_exec_def_two_dim3(gdf: DataFrameFactory):
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[["product_category"], ["region", "state", "measureGroup"]],
    )
    _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(4, 96))


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_totals1.yaml"))
def test_dataframe_for_exec_def_totals1(gdf: DataFrameFactory):
    """
    Execution with column totals; the row dimension has single label
    """
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[["product_category"], ["region", "state", "measureGroup"]],
        totals=[
            TotalDefinition(
                local_id="grand_total1",
                aggregation="sum",
                total_dims=[TotalDimension(idx=1, items=["region", "state", "measureGroup"])],
                metric_local_id="price",
            ),
            TotalDefinition(
                local_id="grand_total2",
                aggregation="max",
                total_dims=[TotalDimension(idx=1, items=["region", "state", "measureGroup"])],
                metric_local_id="order_amount",
            ),
        ],
    )
    _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(6, 96))


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_totals2.yaml"))
def test_dataframe_for_exec_def_totals2(gdf: DataFrameFactory):
    """
    Execution with column totals; the row dimension have two labels; this exercises that the index is
    padded appropriately
    """
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[["region", "product_category"], ["state", "measureGroup"]],
        totals=[
            TotalDefinition(
                local_id="grand_total1",
                aggregation="sum",
                total_dims=[TotalDimension(idx=1, items=["state", "measureGroup"])],
                metric_local_id="price",
            ),
            TotalDefinition(
                local_id="grand_total2",
                aggregation="max",
                total_dims=[TotalDimension(idx=1, items=["state", "measureGroup"])],
                metric_local_id="order_amount",
            ),
        ],
    )
    _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(19, 96))


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_totals3.yaml"))
def test_dataframe_for_exec_def_totals3(gdf: DataFrameFactory):
    """
    Execution with row totals; the column dimension has single label.
    """
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[["region", "state", "measureGroup"], ["product_category"]],
        totals=[
            TotalDefinition(
                local_id="grand_total1",
                aggregation="sum",
                total_dims=[TotalDimension(idx=0, items=["region", "state", "measureGroup"])],
                metric_local_id="price",
            ),
            TotalDefinition(
                local_id="grand_total2",
                aggregation="max",
                total_dims=[TotalDimension(idx=0, items=["region", "state", "measureGroup"])],
                metric_local_id="order_amount",
            ),
        ],
    )
    _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(96, 6))


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_totals4.yaml"))
def test_dataframe_for_exec_def_totals4(gdf: DataFrameFactory):
    """
    Execution with row totals; the column dimension have two label.
    """
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[["state", "measureGroup"], ["region", "product_category"]],
        totals=[
            TotalDefinition(
                local_id="grand_total1",
                aggregation="sum",
                total_dims=[TotalDimension(idx=0, items=["state", "measureGroup"])],
                metric_local_id="price",
            ),
            TotalDefinition(
                local_id="grand_total2",
                aggregation="max",
                total_dims=[TotalDimension(idx=0, items=["state", "measureGroup"])],
                metric_local_id="order_amount",
            ),
        ],
    )
    _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(96, 19))


# TODO - not implemented yet
# def test_dataframe_for_exec_def_totals5(gdf: DataFrameFactory):
#     """
#     Execution with multiple measures row totals; the columns have labels of each measure.
#     """
#     exec_def = ExecutionDefinition(
#         attributes=[
#             Attribute(local_id="a_region", label="region"),
#             Attribute(local_id="a_cat", label="products.category"),
#         ],
#         metrics=[
#             SimpleMetric(local_id="m_price", item=ObjId(id="price", type="fact")),
#             SimpleMetric(local_id="m_quantity", item=ObjId(id="quantity", type="fact")),
#         ],
#         filters=[],
#         dimensions=[["a_region"], ["a_cat", "measureGroup"]],
#         totals=[
#             TotalDefinition(
#                 local_id="grand_total1",
#                 aggregation="sum",
#                 total_dims=[TotalDimension(idx=1, items=["measureGroup"]), TotalDimension(idx=0, items=["a_region"])],
#                 metric_local_id="m_price",
#             ),
#             TotalDefinition(
#                 local_id="grand_total2",
#                 aggregation="sum",
#                 total_dims=[TotalDimension(idx=1, items=["measureGroup"]), TotalDimension(idx=0, items=["a_region"])],
#                 metric_local_id="m_quantity",
#             ),
#         ],
#     )
#     _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(?, ?))


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_one_dim1.yaml"))
def test_dataframe_for_exec_def_one_dim1(gdf: DataFrameFactory):
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[["region", "state", "product_category", "measureGroup"]],
    )
    _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(364, 1))


@gd_vcr.use_cassette(str(_fixtures_dir / "dataframe_for_exec_def_one_dim2.yaml"))
def test_dataframe_for_exec_def_one_dim2(gdf: DataFrameFactory):
    exec_def = ExecutionDefinition(
        attributes=[
            Attribute(local_id="region", label="region"),
            Attribute(local_id="state", label="state"),
            Attribute(local_id="product_category", label="products.category"),
        ],
        metrics=[
            SimpleMetric(local_id="price", item=ObjId(id="price", type="fact")),
            SimpleMetric(local_id="order_amount", item=ObjId(id="order_amount", type="metric")),
        ],
        filters=[],
        dimensions=[[], ["region", "state", "product_category", "measureGroup"]],
    )
    _run_and_validate_results(gdf=gdf, exec_def=exec_def, expected=(1, 364))
