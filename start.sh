#!/bin/sh
start_jack()
{
    # Start jack on given interface
    # Fall back to hw:0 (BCM) if no other audio device detected
    jackd -R -d alsa -d hw:$1 -p 256 || jackd -R -d alsa -d hw:0 -p 512
}

# Kill previously running jackd
killall jackd || echo "No jackd running."
sleep 1

# Start jackd
start_jack 3 &
sleep 1

# Run program
.venv/bin/python3 main.py -v

# Try to exit jackd cleanly
killall jackd
