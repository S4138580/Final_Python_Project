import pyhtml
import Webpage_3_Mission


pyhtml.need_debugging_help = True

pyhtml.MyRequestHandler.pages["/"] = Webpage_3_Mission
pyhtml.MyRequestHandler.pages["/mission"] = Webpage_3_Mission
pyhtml.MyRequestHandler.pages["/mission.html"] = Webpage_3_Mission
pyhtml.MyRequestHandler.pages["/Webpage_3_Mission.html"] = Webpage_3_Mission

pyhtml.host_site()
