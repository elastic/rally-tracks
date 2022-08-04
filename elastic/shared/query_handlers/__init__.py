# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from enum import Enum
from esrally import exceptions

from shared.query_handlers.date_histogram import DateHistogramHandler
from shared.query_handlers.range_query import RangeQueryHandler

"""
    This module is responsible for registering query handlers designed to allow Elasticsearch operators be modified at
    runtime. These handlers are registered under a key, with the value providing a reference to a QueryHandler class
    responsible for handling the operator type. They key itself should be the same as the Elasticsearch operator for 
    which the QueryHandler is designed e.g. "term" or "range". The handler class needs to implement a constructor which 
    takes an instance of an operator body as the first parameter e.g. for "range"
    
    "age": {
        "gte": 10,
        "lte": 20,
        "boost": 2.0
    }
    
    The class implementation is responsible for persisting this dictionary body. It should also implement a "process" 
    method that should modify the dictionary in place when called. This method takes one argument - the current time. 
    This is left to the user to decide how this operator should be handled. 
    The QueryHandler must be registered via the register_handler method.
    
    Before a query is sent to Elasticsearch, the body is parsed and a check made for each operator to see if has a 
    QueryHandler implemented via the is_query_handler. If so, an instance is instantiated via the get_query_handler 
    method. This instance is passed the body and the process method called.
    
"""

__QUERY_HANDLERS = {}


class HandlerType(Enum):
    Range = 1
    Date_Histogram = 2


def register_handler(query_name, handler):
    __QUERY_HANDLERS[query_name] = handler


def get_query_handler(query_name, request_body):
    if is_query_handler(query_name):
        return __QUERY_HANDLERS[query_name](request_body)
    else:
        raise exceptions.TrackConfigError(f"[{query_name}] is not a registered handler")


def is_query_handler(query_name):
    return query_name in __QUERY_HANDLERS


register_handler(HandlerType.Range.name.lower(), RangeQueryHandler)
register_handler(HandlerType.Date_Histogram.name.lower(), DateHistogramHandler)
# register new query handlers here
