echo "export PS1=\"$ \"" >> ~/.bashrc
calcpy -c 'calcpy.reset(False); calcpy.base_currency="usd";'
cp -f $(dirname "$0")/demo_config.py $(ipython locate)/profile_calcpy/ipython_config.py
rm $(ipython locate)/profile_calcpy/history.sqlite
python asciinario.py demo_scenario.txt demo.cast

# remove the export from bashrc
head -n -1 ~/.bashrc > temp.txt ; mv temp.txt ~/.bashrc

# remove [screen is terminating] from recording
head -n -1 demo.cast  > temp.txt ; mv temp.txt demo.cast

termtosvg render -t light_template.svg demo.cast demo_light.svg
termtosvg render -t dark_template.svg demo.cast demo_dark.svg
