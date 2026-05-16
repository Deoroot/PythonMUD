"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit

from .objects import ObjectParent


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property and overrides some hooks
    and methods to represent the exits.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects child classes like this.

    """

    pass


class FareGangwayExit(Exit):
    """
    A boarding gangway exit that charges the traverser a credit fare.

    Set ``self.db.fare`` (int credits) before the exit is used. If the
    traverser cannot afford the fare they are blocked with a message and
    the traversal is aborted. On success the fare is deducted from
    ``traversing_object.db.ledger["credits"]`` before the move.
    """

    def at_traverse(self, traversing_object, target_location, **kwargs):
        fare = int(self.db.fare or 0)
        if fare > 0:
            ledger = traversing_object.db.ledger or {}
            credits = int(ledger.get("credits", 0))
            if credits < fare:
                traversing_object.msg(
                    f"|rPassage costs {fare} credits. You have {credits}.|n"
                )
                return False
            ledger["credits"] = credits - fare
            traversing_object.db.ledger = ledger
            traversing_object.msg(
                f"|y{fare} credits charged for passage.|n  "
                f"Remaining: {ledger['credits']} cr."
            )
        return super().at_traverse(traversing_object, target_location, **kwargs)
