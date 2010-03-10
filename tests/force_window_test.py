

"""
Use this to test that windowing will work in general
"""
__import__("sys").path.append('./')
import window

window.run_with_windowing()
w = window.Window()
w.write("Ohai!")
print "This is the real app!"
__import__("time").sleep(2)
