class EventHook(object):
  def __init__(self):
    self.__handlers = []

  def addHandler(self, handler):
    self.__handlers.append(handler)

  def removeHandler(self, handler):
    self.__handlers.remove(handler)

  def fire(self, *args, **kwargs):
    for handler in self.__handlers:
      handler(*args, **kwargs)

  def clearObjectHandlers(self, inObject):
    for theHandler in self.__handlers:
      if theHandler.im_self == inObject:
        self.removeHandler(theHandler)


class Pizza:
  def __init__(self):
    self.ingredients = []


class Baker:

  def __init__(self):
    self.onPizzaReady = EventHook()

  def makePizza(self):
    p = Pizza()
    self.onPizzaReady.fire(pizza=p)

def pizzaDone(pizza):
  print ("Pizza is done!")
  print ("Ingredients %d " % (len(pizza.ingredients)))

def main():
  b = Baker()
  b.onPizzaReady.addHandler(pizzaDone)
  b.makePizza()

if __name__ == "__main__":
  main()