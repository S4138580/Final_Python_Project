import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

import Python.pyhtml as pyhtml
import Python.Webpage1 as Webpage1
import Python.Webpage3 as Webpage3
import Python.Webpage5 as Webpage5
import Python.Webpage_2_Mission as Webpage_2_Mission
import Python.Webpage_4_Economy as Webpage_4_Economy
import Python.Webpage_6_Average as Webpage_6_Average


pyhtml.need_debugging_help = True

pyhtml.MyRequestHandler.pages["/"] = Webpage1

pyhtml.MyRequestHandler.pages["/Webpage1"] = Webpage1
pyhtml.MyRequestHandler.pages["/Webpage1.html"] = Webpage1

pyhtml.MyRequestHandler.pages["/mission"] = Webpage_2_Mission
pyhtml.MyRequestHandler.pages["/mission.html"] = Webpage_2_Mission
pyhtml.MyRequestHandler.pages["/Webpage_2_Mission.html"] = Webpage_2_Mission

pyhtml.MyRequestHandler.pages["/Webpage3"] = Webpage3
pyhtml.MyRequestHandler.pages["/Webpage3.html"] = Webpage3

pyhtml.MyRequestHandler.pages["/infection-economy"] = Webpage_4_Economy
pyhtml.MyRequestHandler.pages["/Webpage_4_Economy.html"] = Webpage_4_Economy

pyhtml.MyRequestHandler.pages["/Webpage5"] = Webpage5
pyhtml.MyRequestHandler.pages["/Webpage5.html"] = Webpage5

pyhtml.MyRequestHandler.pages["/above-average"] = Webpage_6_Average
pyhtml.MyRequestHandler.pages["/Webpage_6_Average.html"] = Webpage_6_Average

pyhtml.host_site()
