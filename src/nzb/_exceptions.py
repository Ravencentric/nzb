from __future__ import annotations


class NZBException(BaseException):
    """Base exception for all nzb exceptions"""


class InvalidNZBError(NZBException):
    """Invalid NZB"""
