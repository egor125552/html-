#!/bin/bash
xvfb-run --auto-servernum --server-args="-screen 0 640x480x24" bash -c 'python3 calculator/main.py & export APP_PID=$! ; sleep 3 ; scrot calculator_gui.png ; kill $APP_PID'
