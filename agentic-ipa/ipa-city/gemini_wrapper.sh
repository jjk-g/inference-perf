#!/bin/bash
exec gemini --debug "$@" 2>&1 | tee -a /usr/local/google/home/jkramberger/agentic-ipa/ipa-city/gemini_debug.log
