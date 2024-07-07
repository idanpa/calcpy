echo "export PS1=\"$ \"" >> ~/.bashrc
calcpy -c 'calcpy.reset(False); calcpy.base_currency="usd"; calcpy.previewer=False'
cp -f $(dirname "$0")/demo_config.py $(ipython locate)/profile_calcpy/ipython_config.py
rm -f $(ipython locate)/profile_calcpy/history.sqlite
rm -f demo_out
python asciinario.py --type screen demo_scenario.txt demo_out

# using https://github.com/theZiz/aha
# cat demo_out | aha > demo_out.html

# using https://github.com/buildkite/terminal-to-html
cat demo_out | $(dirname "$0")/terminal-to-html -preview > demo_out.html

# todo: wrap the html with svg
#    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
#   <foreignObject x="20" y="20" width="160" height="160">
#     <div>
#	...
#     </div>
#   </foreignObject>
# </svg>

# remove the export from bashrc
head -n -1 ~/.bashrc > temp.txt ; mv temp.txt ~/.bashrc
