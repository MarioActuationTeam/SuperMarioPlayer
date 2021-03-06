import random
import numpy as np

import src.SuperMarioImages as SuperMarioImages
import src.SuperMarioMap as SuperMarioMap
import src.EnumMovement as EnumMovement


##
# This class is responsible for every kind of movement the player makes. It also implements different
# movement strategies.
#
# @author Wolfgang Mair, Florian Weiskirchner, Emmanuel Najfar
# @version 18. January 2021
##

class Movement:

    # List of all possible (rational) inputs the player can make
    COMPLEX_MOVEMENT = [
        ['NOOP'],
        ['right'],
        ['right', 'A'],
        ['right', 'B'],
        ['right', 'A', 'B'],
        ['A'],
        ['left'],
        ['left', 'A'],
        ['left', 'B'],
        ['left', 'A', 'B'],
        ['down'],
        ['up'],
    ]

    # The players X coordinate
    positionMarioRow = 0
    # The players Y coordinate
    positionMarioCole = 0
    # Value to calculate velocity of the player (falling or rising)
    oldYPositionMario = 16
    # True if player is falling
    isFalling = False

    def __init__(self):

        self.sm_images = SuperMarioImages.Images()

        # Needed for better action distribution
        # jumpright 25
        # runright 10
        # jumprunright 65
        # else 0
        self.basicWeights = [0, 0, 25, 10, 65, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.movement = EnumMovement.Movement

    ##
    # DEPRECATED
    # This method lets the player jump the highest he can possibly can.
    # @author Wolfgang Mair
    #
    # @param env The current game environment
    # @param reward Integer which specifies the benefit of an action
    # @param done Boolean which specifies if the game is finished
    # @param info Dictionary which contains information about the environment
    ##
    def bigJump(self, env, reward, done, info):
        height = 0

        # print("Prepare!\n")
        state, reward, done, info = env.step(3)
        env.render()

        while height <= info['y_pos']:

            if done:
                state = env.reset()

            height = info['y_pos']
            state, reward, done, info = env.step(4)

            env.render()
            # print("Jump!\n")

        while height != info['y_pos']:

            if done:
                state = env.reset()

            height = info['y_pos']
            state, reward, done, info = env.step(3)
            env.render()
            # print("Wait!\n")
        return state, reward, done, info

    ##
    # DEPRECATED
    # This method chooses random actions for the player based on a weighted array
    # @author Wolfgang Mair
    #
    # @param weightArray Array of weights to all possible actions the player can take
    ##
    def weightedRandom(self, weightArray):

        listOfValidActionsWithCountOfItemsInferedByWeights = []

        for idx, weight in enumerate(weightArray):
            listOfValidActionsWithCountOfItemsInferedByWeights += [
                                                                      idx] * weight  # inserts "weight"-times an action (= index of operation; see: COMPLEX_MOVEMENT)

        return random.choice(listOfValidActionsWithCountOfItemsInferedByWeights)

    ##
    # DEPRECATED
    # This method tries to identify Goombas and Pits and avoid them with a big jump
    # @author Wolfgang Mair
    #
    # @param state State array provided by the gym-super-mario-bros class of type ndarray:(240, 256, 3)
    # @param env The current game environment
    # @param reward Integer which specifies the benefit of an action
    # @param done Boolean which specifies if the game is finished
    # @param info Dictionary which contains information about the environment
    ##
    def badSearchMovement(self, state, reward, done, info, env):
        maskGoomba = (state[194] == self.sm_images.goombaColor).all(axis=1)
        maskPit = (state[210] == self.sm_images.skyColor).all(axis=1)

        if np.any(maskGoomba):
            return self.bigJump(env, reward, done, info)
        else:
            if np.any(maskPit):
                return self.bigJump(env, reward, done, info)
            else:
                return env.step(self.weightedRandom(self.basicWeights))

    ##
    # Based on the position of Mario, this method looks around him and tries too find other objects
    # @author Florian Weiskirchner
    #
    # @param oldYPositionMario is the Y Position from Mario in the last Move
    # @param doMove Which move should be used from the COMPLEX_MOVEMENT array
    # @param charForMario Which Char Mario has in the array
    # @param isFalling is a bool which is true when Mario is falling and false when he is jumping or running
    # @return doMove gets returned.
    ##
    def goodMovement(self, sm_env):
        self.oldYPositionMario = self.positionMarioRow
        doMove = self.movement.right.value
        self.marioSearch(sm_env)
        self.isFalling = self.checkIfFalling()

        # check whether the square in the same row as and two column in front of mario contains
        # the letter "G" in the array
        # if yes, there is a Goomba in front of mario, therefore the respective function will be called
        if sm_env.environment[self.positionMarioRow, self.positionMarioCole + 2] == "G":
            return self.movementBygoomba()

        # check whether the square in one row under and the same column mario contains
        # the letter "P" in the array
        # if yes, there is a Pipe under mario, therefore the respective function will be called
        if sm_env.environment[self.positionMarioRow + 1, self.positionMarioCole] == "P":
            return self.movementOntopOfPipe()

        # check whether the square in the any row as and one column in front of mario contains
        # the letter "P" in the array
        # if yes, there is a Pipe in front of mario, therefore the respective function will be called
        if (sm_env.environment[:, self.positionMarioCole + 1] == "P").any():
            return self.movementByPipe()

        if sm_env.environment[self.positionMarioRow, self.positionMarioCole + 2] == "C":
            return self.movementByCooper()

        # check whether the square one column in front and one row below mario is empty in the array
        # if yes, there is a pit in front of mario, therefore the respective function will be called
        if sm_env.environment[self.positionMarioRow + 1, self.positionMarioCole + 1] == " ":
            return self.movementByPit()

        # check whether the square in the same row as and one column in front of mario contains
        # the letter "S" in the array
        # if yes, there is a stair in front of mario, therefore the respective function will be called
        if sm_env.environment[self.positionMarioRow, self.positionMarioCole + 1] == "S":
            return self.movementByAscendingStairs()

        # check whether the square in any row and one column in front of mario contains
        # the letter "S" in the array
        # if yes, there is a stair in front of mario, therefore the respective function will be called
        if (sm_env.environment[:, self.positionMarioCole + 1] == "S").any():
            return self.movementByDescendingStairs()

        if self.isFalling:
            doMove = self.movement.left.value
        return doMove

    ##
    # This function search Mario (M) in the Array and saves his position.
    # @author Florian Weiskirchner
    #
    # @param charForMario Which Char Mario has in the array
    # @param positionMarioRow Y position of Mario in the array
    # @param positionMarioCole X position of Mario in the array
    ##
    def marioSearch(self, sm_env):
        charForMario = "M"
        positionMario = np.where(sm_env.environment == charForMario)
        self.positionMarioRow = positionMario[0]
        self.positionMarioCole = positionMario[1]
        return

    ##
    # Checks if Mario is falling based on his current Y position and the last Y position
    # @author Florian Weiskirchner
    #
    # @param oldYPositionMario is the Y Position from Mario in the last Move
    # @param positionMarioRow Y position of Mario in the array
    # @return True or False for isFalling
    ##
    def checkIfFalling(self):
        if self.positionMarioRow > self.oldYPositionMario:
            return True
        return False

    ##
    # Movement from Mario when there is a Gommba in front of him
    # @author Florian Weiskirchner
    #
    # @param movement this is a Enum with the movementoptions from COMPLEX_MOVEMENT
    # @param isFalling is a bool which is true when Mario is falling and false when he is jumping or running
    # @return a value from movement gets returned
    ##
    def movementBygoomba(self):
        if self.isFalling:
            return self.movement.NOOP.value
        return self.movement.rightA.value

    ##
    # NOT USED
    # Movement from Mario when there is a Gommba under him and tries to avoid him
    # @author Florian Weiskirchner
    #
    # @param movement this is a Enum with the movementoptions from COMPLEX_MOVEMENT
    # @return a value from movement gets returned
    ##
    # def avoidGoomba(self):
    # return self.movement.left.value

    ##
    # Movement from Mario when there is a Pipe in front of him
    # @author Florian Weiskirchner
    #
    # @param movement this is a Enum with the movementoptions from COMPLEX_MOVEMENT
    # @param isFalling is a bool which is true when Mario is falling and false when he is jumping or running
    # @return a value from movement gets returned
    ##
    def movementByPipe(self):
        if self.isFalling:
            return self.movement.NOOP.value
        return self.movement.rightAB.value

    ##
    # Movement from Mario when he is on a Pipe
    # @author Florian Weiskirchner
    #
    # @param movement this is a Enum with the movementoptions from COMPLEX_MOVEMENT
    # @param isFalling is a bool which is true when Mario is falling and false when he is jumping or running
    # @return a value from movement gets returned
    ##
    def movementOntopOfPipe(self):
        if self.isFalling:
            return self.movement.NOOP.value
        return self.movement.right.value

    ##
    # Movement from Mario when there is a Cooper in front of him
    # @author Florian Weiskirchner
    #
    # @param movement this is a Enum with the movementoptions from COMPLEX_MOVEMENT
    # @param isFalling is a bool which is true when Mario is falling and false when he is jumping or running
    # @return a value from movement gets returned
    ##
    def movementByCooper(self):
        if self.isFalling:
            return self.movement.NOOP.value
        return self.movement.rightA.value

    ##
    # This method returns the appropriate value for the action that is suited to handling a bottomless pit
    # @author Emmanuel Najfar
    #
    # @param self obligatory parameter
    # @return the value that corresponds to the "jumprunright" action
    ##
    def movementByPit(self):
        return self.movement.rightAB.value

    ##
    # This method returns the appropriate value for the action that is suited to handling the stairs
    # which are made up of "Hard Blocks". These stairs appear in all level types, except for Castle levels.
    # @author Emmanuel Najfar
    #
    # @param self obligatory parameter
    # @return the value that corresponds to the "jumpright" action
    ##
    def movementByAscendingStairs(self):
        if self.isFalling:
            return self.movement.NOOP.value
        return self.movement.rightA.value

    ##
    # This method returns the appropriate value for the action that is suited to handling the descending stairs
    # which are made up of "Hard Blocks". These stairs appear in all level types, except for Castle levels.
    # @author Emmanuel Najfar
    #
    # @param self obligatory parameter
    # @return the value that corresponds to the "jumprunright" action
    ##
    def movementByDescendingStairs(self):
        if self.isFalling:
            return self.movement.NOOP.value
        return self.movement.rightAB.value
