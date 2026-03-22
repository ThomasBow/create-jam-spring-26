while true; do
    python main.py &
    sleep 0.5
    swaymsg fullscreen enable
    wait
done
