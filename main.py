import pyhtml
import Webpage1
import Webpage3
import Webpage5
import Webpage_2_Mission
import Webpage_4_Economy
import Webpage_6_Average


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
