#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 11:39:15 2026

@author: James DAY
"""

from dataclasses import dataclass

@dataclass
class Config:
    CAM = [1]
    PATH_PHOTO = "/dev/shm"