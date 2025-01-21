import queue
from tkinter import Entry
from direct.distributed.DistributedSmoothNode import DistributedSmoothNode
from direct.showbase import ShowBaseGlobal

from direct.actor.Actor import Actor

from panda3d.core import *

class DistributedSmoothActor(DistributedSmoothNode, Actor):
    actors=[]
    def __init__(self, cr):
        Actor.__init__(self)
        DistributedSmoothNode.__init__(self, cr)
        self.setCacheable(True)
        self.setScale(0.1)
        self.ModelName=""
        self.role=None
        DistributedSmoothActor.actors.append(self)

        # 衝突検知オブジェクト
        ShowBaseGlobal.base.cTrav = CollisionTraverser( "traverser" )
        ShowBaseGlobal.base.cTrav.showCollisions( ShowBaseGlobal.base.render )
        
        # 衝突検知モデル
        self.collmodel= CollisionNode("collision")
        self.collmodel.setTag("actor_id", str(id(self)))
        self.collmodel.addSolid(CollisionSphere(0, 0, 0, 5))
        self.coll = self.attachNewNode( self.collmodel )
        self.coll.show()

        handlerevent = CollisionHandlerEvent()
        # 上から衝突時、衝突中、衝突解除
        handlerevent.addInPattern('%fn-into-%in')
        handlerevent.addAgainPattern('%fn-again-%in')
        handlerevent.addOutPattern('%fn-out-%in')

        # イベントに対するハンドラ関数の登録
        self.accept( "collision-into-collision", self.collisionhandler )
        self.accept( "collision-out-collision", self.separatehandler )
        ShowBaseGlobal.base.cTrav.addCollider( self.coll,  handlerevent) # type: ignore
        ShowBaseGlobal.base.cTrav.traverse(ShowBaseGlobal.base.render) # type: ignore


        # pusher = CollisionHandlerPusher()
        # pusher.addCollider(self.coll, self)

    # ハンドラ関数の定義
    def collisionhandler(self,  entry): 
        # if self.isLocal():
            print("entry", entry.getIntoNode().getTag("actor_id"))
            for actor in DistributedSmoothActor.actors:
                if id(actor) == int(entry.getIntoNode().getTag("actor_id")):
                    break
            else:
                raise
            intoActor=actor
            print(self.role)
            print(intoActor.role)
        
        # if(self.role == ):
        #    print("逮捕")
        #     とりまリザルトに飛ばしたい
    def separatehandler(self, entry ): 
        print ("aaaaaa", entry)

    def setModel(self, modelName:str):
        Actor.loadModel(self, "models/"+modelName)
        self.player=Actor.loadModel(self, "models/"+modelName)
        self.ModelName=modelName
    def getModel(self):
        return self.ModelName
    def generate(self):
        DistributedSmoothNode.generate(self)
        self.activateSmoothing(True, False)
        self.startSmooth()

    def announceGenerate(self):
        DistributedSmoothNode.announceGenerate(self)
        self.reparentTo(ShowBaseGlobal.base.render)

    def disable(self):
        # remove all anims, on all parts and all lods
        self.stopSmooth()
        if (not self.isEmpty()):
            Actor.unloadAnims(self, None, None, None)
        DistributedSmoothNode.disable(self)

    def delete(self):
        try:
            self.DistributedActor_deleted
        except:
            self.DistributedActor_deleted = 1
            self.stopPosHprBroadcast()
            DistributedSmoothNode.sendDeleteMsg(self)
            DistributedSmoothNode.delete(self)
            Actor.delete(self)

    def start(self):
        # Let the DistributedSmoothNode take care of broadcasting the
        # position updates several times a second.
        self.startPosHprBroadcast()
    def onRoleChanged(self, roleName:str):
        self.role=roleName
        ShowBaseGlobal.base.messenger.send("role_changed", [self, roleName])
        self.coll.setName(roleName)
        if self.isLocal():
            self.start()
    def sendRole(self, roleName:str):
        self.sendUpdate("onRoleChanged", [roleName,])
        self.onRoleChanged(roleName)
    def loop(self, animName):
        self.sendUpdate("loop", [animName])
        return Actor.loop(self, animName)
    def pose(self, animName, frame):
        self.sendUpdate("pose", [animName, frame])
        return Actor.pose(self, animName, frame)