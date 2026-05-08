"""
conftest.py — pytest 루트 설정.
프로젝트 루트를 sys.path에 추가해 모든 패키지를 임포트 가능하게 한다.
"""
import sys
import os

# 프로젝트 루트를 sys.path 맨 앞에 추가
sys.path.insert(0, os.path.dirname(__file__))
