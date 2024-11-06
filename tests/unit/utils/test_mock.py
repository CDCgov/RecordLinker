from recordlinker.utils import mock as utils


class TestMockTracer:
    def test_start_span(self):
        tracer = utils.MockTracer()
        with tracer.start_span("test_span") as span:
            assert span is None

    def test_start_as_current_span(self):
        tracer = utils.MockTracer()
        with tracer.start_as_current_span("test.span") as span:
            assert span is None
