from pymt import *
from OpenGL.GL import *

import math
import random

class Rectangle(object):
    def __init__(self, x = 0, y = 0, width = 0, height = 0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def _get_right(self):
        return self.x + self.width
    right = property(_get_right)

    def _get_bottom(self):
        return self.y + self.height
    bottom = property(_get_bottom)

class BoidDisplay(MTWidget):
    def __init__(self, **kwargs):
        super(BoidDisplay, self).__init__(**kwargs)
        self.size = (10, 10)
        self.color = map(lambda x: random.random() * 0.2 + 0.6, xrange(3))
        self.color[random.randint(0, 2)] = 0
        if random.random() > 0.5:
            self.color[random.randint(0, 2)] = 0

    def draw(self):
        dir = (self.boid._position - self.boid._oldPosition).normalize()
        a = dir.rotate(-90) * self.size[0] / 5. + self.boid._oldPosition
        b = dir.rotate(90) * self.size[0] / 5. + self.boid._oldPosition
        c = dir * self.size[0] + self.boid._oldPosition

        set_color(*self.color)
        #drawLine([self.boid._oldPosition.x, self.boid._oldPosition.y,
        #          self.boid.x, self.boid.y])
        drawPolygon([a.x, a.y, b.x, b.y, c.x, c.y])

class Boid(object):
    EDGE_NONE = 'none'
    EDGE_WRAP = 'wrap'
    EDGE_BOUNCE = 'bounce'
    ZERO = Vector(0, 0)

    def __init__(self, **kwargs):
        self.extra = {}
        self._maxForce = 1.0
        self._maxForce = 0
        self._maxSpeed = 10.0
        self._distance = 0
        self._drawScale = 0
        self._maxForceSQ = 0
        self._maxSpeedSQ = 0
        self._velocity = Vector(0, 0)
        self._position = Vector(0, 0)
        self._oldPosition = Vector(0, 0)
        self._acceleration = Vector(0, 0)
        self._steeringForce = Vector(0, 0)
        self._renderData = None
        self._edgeBehavior = self.EDGE_NONE
        self._boundsRadius = 0
        self._boundsCentre = Vector(0, 0)
        self._radius = 10.
        self._wanderTheta = 0.
        self._wanderRadius = 16.
        self._wanderDistance = 60.
        self._wanderStep = .25
        self._lookAtTarget = True

        self.reset()

    def _get_x(self):
        return self._position.x
    def _set_x(self, value):
        self._position.x = value
    x = property(_get_x, _set_x)

    def _get_y(self):
        return self._position.y
    def _set_y(self, value):
        self._position.y = value
    y = property(_get_y, _set_y)

    def _get_maxForce(self):
        return self._maxForce
    def _set_maxForce(self, value):
        if value < 0:
            value = 0
        self._maxForce = value
        self._maxForceSQ = value * value
    maxForce = property(_get_maxForce, _set_maxForce)

    def _get_maxSpeed(self):
        return self._maxSpeed
    def _set_maxSpeed(self, value):
        if value < 0:
            value = 0
        self._maxSpeed = value
        self._maxSpeedSQ = value * value
    maxSpeed = property(_get_maxSpeed, _set_maxSpeed)

    def _get_renderData(self):
        return self._renderData
    def _set_renderData(self, value):
        self._renderData = value
        if self._renderData.width > self._renderData.height:
            self._radius = self._renderData.width
        else:
            self._radius = self._renderData.height
        self._renderData.boid = self
    renderData = property(_get_renderData, _set_renderData)

    def _get_edgeBehavior(self):
        return self._edgeBehavior
    def _set_edgeBehavior(self, value):
        if value not in (self.EDGE_NONE, self.EDGE_WRAP, self.EDGE_BOUNCE):
            raise Exception('Invalid edgeBehavior <%s>' % str(value))
        self._edgeBehavior = value
    edgeBehavior = property(_get_edgeBehavior, _set_edgeBehavior)

    def _get_bounds(self):
        return self._bounds
    def _set_bounds(self, value):
        self._bounds = value
        self._customBounds = True
    bounds = property(_get_bounds, _set_bounds)

    def _get_boundsCentre(self):
        return self._boundsCentre
    def _set_boundsCentre(self, value):
        self._boundsCentre = value
    boundsCentre = property(_get_boundsCentre, _set_boundsCentre)

    def _get_boundsRadius(self):
        return self._boundsRadius
    def _set_boundsRadius(self, value):
        self._boundsRadius = value
    boundsRadius = property(_get_boundsRadius, _set_boundsRadius)

    def _get_wanderStep(self):
        return self._wanderStep
    def _set_wanderStep(self, value):
        self._wanderStep = value
    wanderStep = property(_get_wanderStep, _set_wanderStep)

    def _get_wanderDistance(self):
        return self._wanderDistance
    def _set_wanderDistance(self, value):
        self._wanderDistance = value
    wanderDistance = property(_get_wanderDistance, _set_wanderDistance)

    def _get_wanderRadius(self):
        return self._wanderRadius
    def _set_wanderRadius(self, value):
        self._wanderRadius = value
    wanderRadius = property(_get_wanderRadius, _set_wanderRadius)

    def _get_position(self):
        return self._position
    def _set_position(self, value):
        self._position = value
    position = property(_get_position, _set_position)

    def _get_velocity(self):
        return self._velocity
    def _set_velocity(self, value):
        self._velocity = value
    velocity = property(_get_velocity, _set_velocity)

    def _get_lookAtTarget(self):
        return self._lookAtTarget
    def _set_lookAtTarget(self, value):
        self._lookAtTarget = value
    lookAtTarget = property(_get_lookAtTarget, _set_lookAtTarget)


    #
    #  After calling one or more of the Boid's steering methods,
    #  call the update method in order to set the Boid's position
    #  in relation to the force being applied to it as a result of
    #  it's steering behaviors. If the Boid's edgeBehavior property
    #  is anything other than EDGE_NONE (no edge behavior) then the
    #  Boid's position will be modified accordingly after the
    #  steering forces have been applied
    #
    def update(self):
        self._oldPosition.x = self._position.x
        self._oldPosition.y = self._position.y

        self._velocity += self._acceleration

        if self._velocity.length2() > self._maxSpeedSQ:
            self._velocity = self._velocity.normalize()
            self._velocity *= self._maxSpeed

        self._position += self._velocity * getFrameDt() * 20

        self._acceleration.x = 0
        self._acceleration.y = 0

        # TODO check _boundsRadius is NaN (before)
        if self._edgeBehavior == self.EDGE_NONE and self._boundsRadius == 0.:
            return

        if self._position != self._oldPosition:
            distance = self._position.distance(self._boundsCentre)

            if distance > self._boundsRadius + self._radius:
                if self._edgeBehavior == self.EDGE_BOUNCE:
                    #  
                    #  Move the boid to the edge of the boundary
                    #  then invert it's velocity and step it
                    #  forward back into the sphere
                    #  

                    self._position -= self._boundsCentre
                    self._position = self._position.normalize()
                    self._position *= (self._boundsRadius + self._radius)

                    # TODO check, was self._velocity.scaleBy(-1) ?
                    self._velocity *= Vector(-1, -1)
                    self._position += self._velocity
                    self._position += self._boundsCentre

                elif self._edgeBehavior == self.EDGE_WRAP:
                    #  
                    #  Move the Boid to the antipodal point of it's
                    #  current position on the bounding sphere by
                    #  taking the inverse of it's position vector
                    #  

                    self._position -= self._boundsCentre
                    # TODO check, was self._position.negate()
                    self._position *= Vector(-1, -1)
                    self._position += self._boundsCentre

    #
    #  Constrains the Boid to a rectangular area of the screen
    #  by calculating the 2D position of the Boid on the screen,
    #  limiting it to the dimensions of the Rectangle and then
    #  projecting the resulting values back into 3D space
    # 
    #  @param	rect
    # 
    #  The rectangle to constrain the Boid's position to
    # 
    #  @param	behavior
    # 
    #  Since this method is a substitute for the normal
    #  edge behavior, you can specify which behavior the
    #  Boid should use manually
    # 
    #  @param	zMin
    # 
    #  Use this if you wish to constrain the Boid's z
    #  position to a minimum amount
    # 
    #  @param	zMax
    # 
    #  Use this if you wish to constrain the Boid's z
    #  position to a maximum amount
    # 
    #

    def constrainToRect(self, rect, behavior = EDGE_BOUNCE):
        if not self._renderData:
            return

        if self._position.x < rect.left - self._radius:
            if behavior == self.EDGE_WRAP:
                self._position.x = rect.right

            elif behavior == self.EDGE_BOUNCE:
                self._position.x = rect.left
                self._velocity.x *= -1

        elif self._position.x > rect.right + self._radius:
            if behavior == self.EDGE_WRAP:
                self._position.x = rect.left

            if behavior == self.EDGE_BOUNCE:
                self._position.x = rect.right
                self._velocity.x *= -1

        if self._position.y < rect.top - self._radius:
            if behavior == self.EDGE_WRAP:
                self._position.y = rect.bottom

            elif behavior == self.EDGE_BOUNCE:
                self._position.y = rect.top
                self._velocity.y *= -1

        elif self._position.y > rect.bottom + self._radius:
            if behavior == self.EDGE_WRAP:
                self._position.y = rect.top

            elif behavior == self.EDGE_BOUNCE:
                self._position.y = rect.bottom
                self._velocity.y *= -1


    #  
    #  Applies a braking force to the boid by scaling it's
    #  velocity.
    # 
    #  @param	brakingForce
    # 
    #  A number between 0 and 1. 0 = no effect
    #  

    def brake(self, brakingForce = .01):
        self._velocity *= 1 - brakingForce

    #  
    #  Seeks the Boid towards the specified target
    # 
    #  @param	target
    # 
    #  The target for the Boid to seek
    # 
    #  @param	multiplier
    # 
    #  By multiplying the force generated by this behavior,
    #  more or less weight can be given to this behavior in
    #  comparison to other behaviors being calculated by the
    #  Boid. To increase the weighting of this behavior, use
    #  a number above 1.0, or to decrease it use a number
    #  below 1.0
    #  

    def seek(self, target, multiplier = 1.0):
        self._steeringForce = self.steer(target)

        if multiplier != 1.0:
            self._steeringForce *= multiplier

        self._acceleration += self._steeringForce

    #  
    #  Seeks the Boid towards the specified target and
    #  applies a deceleration force as the Boid arrives
    # 
    #  @param	target
    # 
    #  The target for the Boid to seek
    # 
    #  @param	easeDistance
    # 
    #  The distance from the target at which the Boid should
    #  begin to decelerate
    # 
    #  @param	multiplier
    # 
    #  By multiplying the force generated by this behavior,
    #  more or less weight can be given to this behavior in
    #  comparison to other behaviors being calculated by the
    #  Boid. To increase the weighting of this behavior, use
    #  a number above 1.0, or to decrease it use a number
    #  below 1.0
    #  

    def arrive(self, target, easeDistance = 100., multiplier = 1.0):
        self._steeringForce = self.steer(target, True, easeDistance)
        if multiplier != 1.0:
            self._steeringForce *= multiplier

        self._acceleration += self._steeringForce

    #
    #  If a target is within a certain range of the Boid, as
    #  specified by the panicDistance parameter, the Boid will
    #  steer to avoid contact with the target
    # 
    #  @param	target
    # 
    #  The target for the Boid to avoid
    # 
    #  @param	panicDistance
    # 
    #  If the distance between the Boid and the target position
    #  is greater than this value, the Boid will ignore the
    #  target and it's steering force will be unchanged
    # 
    #  @param	multiplier
    # 
    #  By multiplying the force generated by this behavior,
    #  more or less weight can be given to this behavior in
    #  comparison to other behaviors being calculated by the
    #  Boid. To increase the weighting of this behavior, use
    #  a number above 1.0, or to decrease it use a number
    #  below 1.0
    #

    def flee(self, target, panicDistance = 100., multiplier = 1.0):
        self._distance = self._position.distance(target)

        if self._distance > panicDistance:
            return

        self._steeringForce = self.steer(target, True, -panicDistance)

        if multiplier != 1.0:
            self._steeringForce *= multiplier

        self._steeringForce *= -1
        self._acceleration += _steeringForce

    #  
    #  Generates a random wandering force for the Boid.
    #  The results of this method can be controlled by the
    #  _wanderDistance, _wanderStep and _wanderRadius parameters
    # 
    #  @param	multiplier
    # 
    #  By multiplying the force generated by this behavior,
    #  more or less weight can be given to this behavior in
    #  comparison to other behaviors being calculated by the
    #  Boid. To increase the weighting of this behavior, use
    #  a number above 1.0, or to decrease it use a number
    #  below 1.0
    #  

    def wander(self, multiplier = 1.0):
        self._wanderTheta += random.random() * self._wanderStep

        if random.random() < 0.5:
            self._wanderTheta = -self._wanderTheta

        pos = Vector(self._velocity.x, self._velocity.y)

        pos = pos.normalize()
        pos *= self._wanderDistance
        pos += self._position

        offset = Vector(self._wanderRadius * math.cos(self._wanderTheta),
                        self._wanderRadius * math.sin(self._wanderTheta))

        self._steeringForce = self.steer(pos + offset)

        if multiplier != 1.0:
            self._steeringForce *= multiplier

        self._acceleration += self._steeringForce

    #
    #  Use this method to simulate flocking movement in a
    #  group of Boids. Flock will combine the separate,
    #  align and cohesion steering behaviors to produce
    #  the flocking effect. Adjusting the weighting of each
    #  behavior, as well as the distance values for each
    #  can produce distinctly different flocking behaviors
    # 
    #  @param	boids
    # 
    #  An Array of Boids to consider when calculating the
    #  flocking behavior
    # 
    #  @param	separationWeight
    # 
    #  The weighting given to the separation behavior
    # 
    #  @param	alignmentWeight
    # 
    #  The weighting given to the alignment bahavior
    # 
    #  @param	cohesionWeight
    # 
    #  The weighting given to the cohesion bahavior
    # 
    #  @param	separationDistance
    # 
    #  The distance which each Boid will attempt to maintain
    #  between itself and any other Boid in the flock
    # 
    #  @param	alignmentDistance
    # 
    #  If another Boid is within this distance, this Boid will
    #  consider the other Boid's heading when adjusting it's own
    # 
    #  @param	cohesionDistance
    # 
    #  If another Boid is within this distance, this Boid will
    #  consider the other Boid's position when adjusting it's own
    # 
    #  @param	multiplier
    # 
    #  By multiplying the force generated by this behavior,
    #  more or less weight can be given to this behavior in
    #  comparison to other behaviors being calculated by the
    #  Boid. To increase the weighting of this behavior, use
    #  a number above 1.0, or to decrease it use a number
    #  below 1.0
    #

    def flock(self, boids, separationWeight = 0.5, alignmentWeight = 0.1,
              cohesionWeight = 0.2, separationDistance = 100.0,
              alignmentDistance = 200.0, cohesionDistance = 200.0):
        self.separate(boids, separationDistance, separationWeight)
        self.align(boids, alignmentDistance, alignmentWeight)
        self.cohesion(boids, cohesionDistance, cohesionWeight)

    #
    #  Separation will attempt to ensure that a certain distance
    #  is maintained between any given Boid and others in the flock
    # 
    #  @param	boids
    # 
    #  An Array of Boids to consider when calculating the behavior
    # 
    #  @param	separationDistance
    # 
    #  The distance which the Boid will attempt to maintain between
    #  itself and any other Boid in the flock
    # 
    #  @param	multiplier
    # 
    #  By multiplying the force generated by this behavior,
    #  more or less weight can be given to this behavior in
    #  comparison to other behaviors being calculated by the
    #  Boid. To increase the weighting of this behavior, use
    #  a number above 1.0, or to decrease it use a number
    #  below 1.0
    #

    def separate(self, boids, separationDistance = 50.0, multiplier = 1.0 ):
        self._steeringForce = self.getSeparation(boids, separationDistance)

        if multiplier != 1.0:
            self._steeringForce *= multiplier

        self._acceleration += self._steeringForce

    #
    #  Align will correct the Boids heading in order for it
    #  to point in the average direction of the flock
    # 
    #  @param	boids
    # 
    #  An Array of Boids to consider when calculating the behavior
    # 
    #  @param	neighborDistance
    # 
    #  If another Boid is within this distance, this Boid will
    #  consider the other Boid's heading when adjusting it's own
    # 
    #  @param	multiplier
    # 
    #  By multiplying the force generated by this behavior,
    #  more or less weight can be given to this behavior in
    #  comparison to other behaviors being calculated by the
    #  Boid. To increase the weighting of this behavior, use
    #  a number above 1.0, or to decrease it use a number
    #  below 1.0
    #

    def align(self, boids, neighborDistance = 40.0, multiplier = 1.0 ):
        self._steeringForce = self.getAlignment(boids, neighborDistance)

        if multiplier != 1.0:
            self._steeringForce *= multiplier

        self._acceleration += self._steeringForce

    #  
    #  Cohesion will attempt to make all Boids in the flock converge
    #  on a point which lies at the centre of the flock
    # 
    #  @param	boids
    # 
    #  An Array of Boids to consider when calculating the behavior
    # 
    #  @param	neighborDistance
    # 
    #  If another Boid is within this distance, this Boid will
    #  consider the other Boid's position when adjusting it's own
    # 
    #  @param	multiplier
    # 
    #  By multiplying the force generated by this behavior,
    #  more or less weight can be given to this behavior in
    #  comparison to other behaviors being calculated by the
    #  Boid. To increase the weighting of this behavior, use
    #  a number above 1.0, or to decrease it use a number
    #  below 1.0
    #  

    def cohesion(self, boids, neighborDistance = 10.0, multiplier = 1.0 ):
        self._steeringForce = self.getCohesion(boids, neighborDistance)

        if multiplier != 1.0:
            self._steeringForce *= multiplier

        self._acceleration += self._steeringForce

    #
    #  Resets the Boid's position, velocity, acceleration and
    #  current steering force to zero
    #

    def reset(self):
        self._velocity = Vector(0, 0)
        self._position = Vector(0, 0)
        self._oldPosition = Vector(0, 0)
        self._acceleration = Vector(0, 0)
        self._steeringForce = Vector(0, 0)

    def steer(self, target, ease = False, easeDistance = 100):
        self._steeringForce = target - self._position

        self._distance = self._steeringForce.length()
        self._steeringForce = self._steeringForce.normalize()

        if self._distance > 0.00001:
            if self._distance < easeDistance and ease:
                self._steeringForce *= (self._maxSpeed * ( self._distance / easeDistance ))
            else:
                self._steeringForce *= self._maxSpeed

            self._steeringForce -= self._velocity

            if self._steeringForce.length2() > self._maxForceSQ:
                self._steeringForce = self._steeringForce.normalize()
                self._steeringForce *= self._maxForce

        return self._steeringForce

    def getSeparation(self, boids, separation = 25.0):
        force = Vector(0, 0)
        difference = Vector(0, 0)
        count = 0

        for boid in boids:
            distance = _position.distance(boid.position)

            if distance > 0 and distance < separation:
                difference = self._position - boid.position
                difference = difference.normalize()
                difference *= 1 / distance

                force += difference
                count += 1

        if count > 0:
            force *= 1 / count

        return force

    def getAlignment(self, boids, neighborDistance = 50.0):
        force = Vector(0, 0)
        count = 0

        for boid in boids:
            distance = _position.distance(boid.position)

            if distance > 0 and distance < neighborDistance:
                force += boid.velocity
                count += 1

        if count > 0:
            force *= 1 / count

            if force.length2() > self._maxForceSQ:
                force = force.normalize()
                force *= self._maxForce

        return force

    def getCohesion(self, boids, neighborDistance = 50.0):
        force = Vector(0, 0)
        count = 0

        for boid in boids:
            distance = _position.distance(boid.position)

            if distance > 0 and distance < neighborDistance:
                force += boid.position
                count += 1

        if count > 0:
            force *= 1 / count
            force = self.steer(force)
            return force

        return force

class AbstractDemo(MTWidget):
    def __init__(self, **kwargs):
        super(AbstractDemo, self).__init__(**kwargs)
        self.boids = []
        self.config = {
            'minForce': 3.0,
            'maxForce': 6.0,
            'minSpeed': 6.0,
            'maxSpeed': 12.0,
            'minWanderDistance': 10.0,
            'maxWanderDistance': 100.0,
            'minWanderRadius': 5.0,
            'maxWanderRadius': 20.0,
            'minWanderStep': 0.1,
            'maxWanderStep': 0.9,
            'boundsRadius': 250,
            'numBoids': 120
        }

    def createBoid(self):
        boid = Boid()
        self.setProperties(boid)
        boid.renderData = BoidDisplay()
        self.boids.append(boid)

    def createBoids(self, count=100):
        for i in xrange(count):
            self.createBoid()

    def setProperties(self, boid):
        w = self.get_parent_window()
        boid.edgeBehavior = Boid.EDGE_BOUNCE
        boid.maxForce = random.uniform(self.config['minForce'],
                                       self.config['maxForce'])
        boid.maxSpeed = random.uniform(self.config['minSpeed'],
                                       self.config['maxSpeed'])
        boid.wanderDistance = random.uniform(self.config['minWanderDistance'],
                                             self.config['maxWanderDistance'])
        boid.wanderStep = random.uniform(self.config['minWanderStep'],
                                         self.config['maxWanderStep'])
        boid.wanderRadius = random.uniform(self.config['minWanderRadius'],
                                           self.config['maxWanderRadius'])

        boid.boundsRadius = w.width * 0.6
        boid.boundsCentre = Vector(w.width / 2., w.height / 2.)
        if boid.x == 0 and boid.y == 0:
            boid.x = boid.boundsCentre.x + random.randint(-100, 100)
            boid.y = boid.boundsCentre.y + random.randint(-100, 100)
            vel = Vector(random.uniform(-2., 2.), random.uniform(-2., 2.))
            boid.velocity += vel

    def updateBoid(self, boid):
        pass

    def draw(self):
        for boid in self.boids:
            self.updateBoid(boid)
            boid.renderData.draw()

class WanderDemo(AbstractDemo):
    def __init__(self, **kwargs):
        super(WanderDemo, self).__init__(**kwargs)
        self.panicDistance = 120

    def updateBoid(self, boid):
        touches = getCurrentTouches()
        for touch in touches:
            obj = Vector(touch.x, touch.y)
            distance = boid.position.distance(obj)
            if distance > self.panicDistance:
                pass
            else:
                boid.arrive(obj, 5, 1)
        boid.wander()
        boid.update()


if __name__ == '__main__':
    m = MTWindow()
    demo = WanderDemo()
    m.add_widget(demo)
    demo.createBoids(75)
    runTouchApp()
