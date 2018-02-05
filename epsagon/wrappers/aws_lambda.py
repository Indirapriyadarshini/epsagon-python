"""
Wrapper for AWS Lambda.
"""

from __future__ import absolute_import
import traceback
import time
import functools
from ..trace import tracer
from ..runners.aws_lambda import LambdaRunner
from ..triggers.aws_lambda import LambdaTriggerFactory
from .. import constants


def lambda_wrapper(func):
    """Epsagon's Lambda wrapper."""

    @functools.wraps(func)
    def _lambda_wrapper(*args, **kwargs):
        tracer.prepare()
        event, context = args

        try:
            tracer.events.append(
                LambdaTriggerFactory.factory(time.time(), event)
            )
        except Exception as exception:
            tracer.add_exception(exception, traceback.format_exc())

        runner = LambdaRunner(time.time(), context)
        tracer.events.append(runner)
        constants.COLD_START = False

        try:
            result = func(*args, **kwargs)
            return result

        except Exception as exception:
            tracer.add_exception(exception, traceback.format_exc())
            raise

        finally:
            runner.terminate()
            tracer.send_traces()

    return _lambda_wrapper
