#!/bin/bash

# This script returns the available memory in home directory in bytes
df --output="avail" / | tail -1
