class MockTracer:
    """
    A no-op OTel tracer that can be used in place of a real tracer. This is useful
    for situations where users decide to not install the otelemetry package.
    """

    def start_as_current_span(self, name, **kwargs):
        """Returns a no-op span"""
        return self

    def __enter__(self):
        """No-op for context manager entry"""
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """No-op for context manager exit"""
        pass

    def start_span(self, name, **kwargs):
        """Returns a no-op span"""
        return self
