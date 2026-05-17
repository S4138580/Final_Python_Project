import pyhtml
import Webpage_2_Mission
import Webpage_4_Economy
import Webpage_6_Average


pyhtml.need_debugging_help = True

pyhtml.MyRequestHandler.pages["/"] = Webpage_2_Mission
pyhtml.MyRequestHandler.pages["/mission"] = Webpage_2_Mission
pyhtml.MyRequestHandler.pages["/mission.html"] = Webpage_2_Mission
pyhtml.MyRequestHandler.pages["/Webpage_2_Mission.html"] = Webpage_2_Mission
pyhtml.MyRequestHandler.pages["/infection-economy"] = Webpage_4_Economy
pyhtml.MyRequestHandler.pages["/Webpage_4_Economy.html"] = Webpage_4_Economy
pyhtml.MyRequestHandler.pages["/above-average"] = Webpage_6_Average
pyhtml.MyRequestHandler.pages["/Webpage_6_Average.html"] = Webpage_6_Average

pyhtml.host_site()
