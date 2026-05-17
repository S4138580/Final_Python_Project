import pyhtml
import Webpage1
import Webpage3
import Webpage5


pyhtml.need_debugging_help = True
pyhtml.MyRequestHandler.pages["/Webpage1.html"] = Webpage1
pyhtml.MyRequestHandler.pages["/"] = Webpage1
pyhtml.MyRequestHandler.pages["/Webpage1"] = Webpage1


# pyhtml.MyRequestHandler.pages["/Webpage2"] = Webpage2
# pyhtml.MyRequestHandler.pages["/Webpage2.html"] = Webpage2

pyhtml.MyRequestHandler.pages["/Webpage3"] = Webpage3
pyhtml.MyRequestHandler.pages["/Webpage3.html"] = Webpage3

pyhtml.MyRequestHandler.pages["/Webpage5"] = Webpage5
pyhtml.MyRequestHandler.pages["/Webpage5.html"] = Webpage5

pyhtml.host_site()