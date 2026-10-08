from pc6 import *
import statistics
ROOM={0:(141,121),1:(141,125),2:(139,119),3:(139,127),4:(137,123),5:(142,129),6:(135,118),7:(135,128),8:(143,117)}
def room_cells(names):
    return {n: ROOM[k] for k,n in enumerate(names)}
def food(n):
    g=rm.call("get_pawn", id=ids()[n], tab="needs")
    return {x["label"]:x["percent"] for x in g.get("needs",[])}.get("Food")
def feed(names, below=30):
    """Order each pawn under `below` % food to consume a survival meal from the pile."""
    meals=rm.call("list_things", category="item", defName="MealSurvivalPack", verbose=True, confirm=True)["things"]
    if not meals: return "no meals"
    fed=[]
    for n in names:
        f=food(n)
        if f is not None and f<below:
            m=min(meals, key=lambda t: 0)
            opts=rm.call("order_pawn", id=ids()[n], targetId=m["id"]).get("options",[])
            o=next((o for o in opts if o["label"].lower().startswith("consume") and not o.get("disabled")), None)
            if o and rm.call("order_pawn", id=ids()[n], targetId=m["id"], index=o["index"]).get("executed"): fed.append((n,f))
    return fed
