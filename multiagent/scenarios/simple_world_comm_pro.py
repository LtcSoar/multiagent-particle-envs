from asyncio import FastChildWatcher
import numpy as np
from multiagent.core import World, Agent, Landmark,Entity
from multiagent.scenario import BaseScenario


class Scenario(BaseScenario):
    def make_world(self):
        world = World()
        # set any world properties first
        world.dim_c = 4
        #world.damping = 1
        num_good_agents = 6
        num_adversaries = 3
        num_agents = num_adversaries + num_good_agents
        num_landmarks = 1
        num_food = 1
        num_forests = 2

        #编队
        world.team = [[0,2,3],[1,4,5]]
        #world.team = [[0, 2, 3, 4], [1, 5, 6, 7]]

        #吃到食物flag
        world.food_flag = False

        # add agents
        world.agents = [Agent() for i in range(num_agents)]
        for i, agent in enumerate(world.agents):
            agent.name = 'agent %d' % i
            agent.collide = True
            agent.leader = True if i < 2 else False
            #agent.leader = True


            agent.silent = True if i > 1 else False
            # agent.silent = False

            agent.adversary = True if i >= num_good_agents else False
            #agent.size = 0.075 if agent.adversary else 0.045
            agent.size = 0.05
            agent.accel = 4.0 if agent.adversary else 3.0
            #agent.accel = 20.0 if agent.adversary else 25.0
            agent.max_speed = 1.3 if agent.adversary else 1.0
            # 红色 adv 防守方
            # 绿色 good 进攻

        # add landmarks
        world.landmarks = [Landmark() for i in range(num_landmarks)]
        for i, landmark in enumerate(world.landmarks):
            landmark.name = 'landmark %d' % i
            landmark.collide = True
            landmark.movable = False
            landmark.size = 0.2
            landmark.boundary = False
        world.food = [Landmark() for i in range(num_food)]
        for i, landmark in enumerate(world.food):
            landmark.name = 'food %d' % i
            landmark.collide = False
            landmark.movable = False
            landmark.size = 0.03
            landmark.boundary = False
        world.forests = [Landmark() for i in range(num_forests)]
        for i, landmark in enumerate(world.forests):
            landmark.name = 'forest %d' % i
            landmark.collide = False
            landmark.movable = False
            landmark.size = 0.3
            landmark.boundary = False
        world.landmarks += world.food
        world.landmarks += world.forests
        #world.landmarks += self.set_boundaries(world)  # world boundaries now penalized with negative reward
        # make initial conditions
        self.reset_world(world)
        return world

    def set_boundaries(self, world):
        boundary_list = []
        landmark_size = 1
        edge = 1 + landmark_size
        num_landmarks = int(edge * 2 / landmark_size)
        for x_pos in [-edge, edge]:
            for i in range(num_landmarks):
                l = Landmark()
                l.state.p_pos = np.array([x_pos, -1 + i * landmark_size])
                boundary_list.append(l)

        for y_pos in [-edge, edge]:
            for i in range(num_landmarks):
                l = Landmark()
                l.state.p_pos = np.array([-1 + i * landmark_size, y_pos])
                boundary_list.append(l)

        for i, l in enumerate(boundary_list):
            l.name = 'boundary %d' % i
            l.collide = True
            l.movable = False
            l.boundary = True
            l.color = np.array([0.75, 0.75, 0.75])
            l.size = landmark_size
            l.state.p_vel = np.zeros(world.dim_p)

        return boundary_list


    def reset_world(self, world):
        # random properties for agents
        for i, agent in enumerate(world.agents):
            agent :Agent
            agent.color = np.array([0.45, 0.95, 0.45]) if not agent.adversary else np.array([0.95, 0.45, 0.45])
            agent.color -= np.array([0.4, 0.4, 0.4]) if agent.leader else np.array([0, 0, 0])
            agent.accel = 4.0 if agent.adversary else 3.0
            # agent.accel = 20.0 if agent.adversary else 25.0
            agent.max_speed = 1.3 if agent.adversary else 1.0
            agent.leader = True if i < 2 else False
            agent.silent = True if i > 1 else False
            agent.collide = True
            agent.dead = False
            # random properties for landmarks

        world.team = [[0,2,3],[1,4,5]]
        world.food_flag = False


        for i, landmark in enumerate(world.landmarks):
            landmark.color = np.array([0.25, 0.25, 0.25])
        for i, landmark in enumerate(world.food):
            landmark.color = np.array([0.15, 0.15, 0.65])
        for i, landmark in enumerate(world.forests):
            landmark.color = np.array([0.6, 0.9, 0.6])
        # set random initial states
        for agent in world.agents:
            agent.state.p_pos = np.random.uniform(-1, +1, world.dim_p)
            agent.state.p_vel = np.zeros(world.dim_p)
            agent.state.c = np.zeros(world.dim_c)
        for i, landmark in enumerate(world.landmarks):
            landmark.state.p_pos = np.random.uniform(-0.9, +0.9, world.dim_p)
            landmark.state.p_vel = np.zeros(world.dim_p)
        for i, landmark in enumerate(world.food):
            landmark.state.p_pos = np.random.uniform(-0.9, +0.9, world.dim_p)
            landmark.state.p_vel = np.zeros(world.dim_p)
        for i, landmark in enumerate(world.forests):
            landmark.state.p_pos = np.random.uniform(-0.9, +0.9, world.dim_p)
            landmark.state.p_vel = np.zeros(world.dim_p)

    def benchmark_data(self, agent, world):
        if agent.adversary:
            collisions = 0
            for a in self.good_agents(world):
                if self.is_collision(a, agent):
                    collisions += 1
            return collisions
        else:
            return 0


    def is_collision(self, agent1: Entity, agent2:Entity):
        delta_pos = agent1.state.p_pos - agent2.state.p_pos
        dist = np.sqrt(np.sum(np.square(delta_pos)))
        dist_min = agent1.size + agent2.size
        return True if dist < dist_min else False


    # return all agents that are not adversaries
    def good_agents(self, world: World):
        return [agent for agent in world.agents if not agent.adversary]

    # return all adversarial agents
    def adversaries(self, world : World):
        return [agent for agent in world.agents if agent.adversary]


    def reward(self, agent : Agent, world : World):
        # Agents are rewarded based on minimum agent distance to each landmark
        #boundary_reward = -10 if self.outside_boundary(agent) else 0
        main_reward = self.adversary_reward(agent, world) if agent.adversary else self.agent_reward(agent, world)
        return main_reward

    def outside_boundary(self, agent):
        if agent.state.p_pos[0] > 1 or agent.state.p_pos[0] < -1 or agent.state.p_pos[1] > 1 or agent.state.p_pos[1] < -1:
            return True
        else:
            return False

    #红色 adv 防守方 3
    #绿色 good 进攻 6
    def agent_reward(self, agent : Agent, world :World): #绿色
        # Agents are rewarded based on minimum agent distance to each landmark
        if agent.dead:
            return 0
        rew = 0
        shape = False
        adversaries = self.adversaries(world)
        if shape:
            for adv in adversaries:
                rew += 0.1 * np.sqrt(np.sum(np.square(agent.state.p_pos - adv.state.p_pos)))
        if agent.collide:
            for a in adversaries:
                if self.is_collision(a, agent):
                    rew -= 5
                    agent.dead = True
                    # agent.accel = 0.0
                    # agent.max_speed = 0.0

        def bound(x):
            if x < 0.9:
                return 0
            if x < 1.0:
                return (x - 0.9) * 10
            return min(np.exp(2 * x - 2), 10)  # 1 + (x - 1) * (x - 1)

        for p in range(world.dim_p):
            x = abs(agent.state.p_pos[p])
            rew -= 2 * bound(x)

        # 这个if world.food_flag暂时只适用于单个food场景，否则flag判断应更复杂
        if world.food_flag:
            rew += 100
        else:
            for food in world.food:
                if self.is_collision(agent, food):
                    rew += 100
                    world.food_flag = True
        #按照我的想法，rew应当是负的呀 
        rew -= 0.05 * min([np.sqrt(np.sum(np.square(food.state.p_pos - agent.state.p_pos))) for food in world.food])

        return rew

    def adversary_reward(self, agent : Agent, world : World):
        # Agents are rewarded based on minimum agent distance to each landmark
        rew = 0
        shape = True
        agents = self.good_agents(world)
        adversaries = self.adversaries(world)
        last_live_agents = [] # agents that were alive last seen
        live_agents = [] # agents that are alive after this step
        for a in agents:
            if a.max_speed >= 0.1:
                last_live_agents.append(a)
            if a.dead == False:
                live_agents.append(a)
        if shape :
            if len(live_agents) > 0:
                # print(len(live_agents))
                rew -= 0.05 * min([np.sqrt(np.sum(np.square(a.state.p_pos - agent.state.p_pos))) for a in last_live_agents]) # 这里用last_live_agents相当于增加碰撞奖励
            else:
                rew += 20
        def bound(x):
            if x < 1.0:
                return 0
            return min(np.exp(2 * x - 2), 10)  # 1 + (x - 1) * (x - 1)

        for p in range(world.dim_p):
            x = abs(agent.state.p_pos[p])
            rew -= 2 * bound(x)
            
            
        if agent.collide:
            for ag in last_live_agents:
                # 这里用所有adv的意思是，adv们是一个合作关系
                for adv in adversaries:
                    if self.is_collision(ag, adv):
                        rew += 20
                        ag.accel = 0.0
                        ag.max_speed = 0.0
                        # 加这一步避免后续碰撞的时候对adv运行轨迹的影响
                        ag.collide = False

        # for ag in agents:
        #     for food in world.food:
        #         if self.is_collision(agent, food):
        #             rew -= 100
        #             break
        # 注意顺序是：从good agent到adv，obs和reward依次给出
        if world.food_flag:
            rew -= 100
        return rew


    def observation2(self, agent, world):
        """
        get positions of all entities in this agent's reference frame regardless of forests
        Args:
            agent (Agent): policy agent
            world (World): env

        Returns:
            np.ndarray: agent's obs(regardless of forests)
        """
        
        entity_pos = []
        for entity in world.landmarks:
            if not entity.boundary:
                entity_pos.append(entity.state.p_pos - agent.state.p_pos)

        food_pos = []
        for entity in world.food:
            if not entity.boundary:
                food_pos.append(entity.state.p_pos - agent.state.p_pos)
        # communication of all other agents
        comm = []
        other_pos = []
        other_vel = []
        for other in world.agents:
            if other is agent: continue
            comm.append(other.state.c)
            other_pos.append(other.state.p_pos - agent.state.p_pos)
            if not other.adversary:
                other_vel.append(other.state.p_vel)
        return np.concatenate([agent.state.p_vel] + [agent.state.p_pos] + entity_pos + other_pos + other_vel)
    
    
    def observation(self, agent : Agent, world : World):
        # get positions of all entities in this agent's reference frame
        entity_pos = []
        for entity in world.landmarks:
            if not entity.boundary:
                entity_pos.append(entity.state.p_pos - agent.state.p_pos)

        in_forest = [np.array([-1]), np.array([-1])]
        inf1 = False
        inf2 = False
        if self.is_collision(agent, world.forests[0]):
            in_forest[0] = np.array([1])
            inf1= True
        if self.is_collision(agent, world.forests[1]):
            in_forest[1] = np.array([1])
            inf2 = True

        food_pos = []
        for entity in world.food:
            if not entity.boundary:
                food_pos.append(entity.state.p_pos - agent.state.p_pos)
        # communication of all other agents
        # comm = []
        other_pos = []
        other_vel = []
        for other in world.agents:
            if other is agent: continue
            # comm.append(other.state.c)
            oth_f1 = self.is_collision(other, world.forests[0])
            oth_f2 = self.is_collision(other, world.forests[1])
            if (inf1 and oth_f1) or (inf2 and oth_f2) or (not inf1 and not oth_f1 and not inf2 and not oth_f2) or agent.leader:  #without forest vis
                other_pos.append(other.state.p_pos - agent.state.p_pos)
                # if not other.adversary:
                other_vel.append(other.state.p_vel)
            else:
                other_pos.append([0, 0])
                # if not other.adversary:
                other_vel.append([0, 0])

        # to tell the pred when the prey are in the forest
        # prey_forest = []
        # ga = self.good_agents(world)
        # for a in ga:
        #     if any([self.is_collision(a, f) for f in world.forests]):
        #         prey_forest.append(np.array([1]))
        #     else:
        #         prey_forest.append(np.array([-1]))
        # to tell leader when pred are in forest
        # prey_forest_lead = []
        # for f in world.forests:
        #     if any([self.is_collision(a, f) for a in ga]):
        #         prey_forest_lead.append(np.array([1]))
        #     else:
        #         prey_forest_lead.append(np.array([-1]))
    
        comm1 = world.agents[world.team[0][0]].state.c
        if world.agents[world.team[0][0]].dead:
            comm1 = np.zeros_like(comm1)
        comm2 = world.agents[world.team[1][0]].state.c
        if world.agents[world.team[1][0]].dead:
            comm2 = np.zeros_like(comm2)
        # 0:23 1:45
        if agent.adversary:
            return np.concatenate([agent.state.p_vel] + [agent.state.p_pos] + entity_pos + other_pos + in_forest + other_vel)
        # elif agent.leader:
        #     if int(agent.name[-1]) == world.team[0][0]:
        #         return np.concatenate([agent.state.p_vel] + [agent.state.p_pos] + entity_pos + other_pos + other_vel + in_forest + comm1)
        #     else:
        #         return np.concatenate([agent.state.p_vel] + [agent.state.p_pos] + entity_pos + other_pos + other_vel + in_forest + comm2)
        else:
            if int(agent.name[-1]) in world.team[0]:
                obs = np.concatenate([agent.state.p_vel] + [agent.state.p_pos] + entity_pos + other_pos + other_vel + in_forest + [comm1])
                if agent.dead:
                    return np.zeros_like(obs)
                return obs
            else:
                obs = np.concatenate([agent.state.p_vel] + [agent.state.p_pos] + entity_pos + other_pos + other_vel + in_forest + [comm2])
                if agent.dead:
                    return np.zeros_like(obs)
                return obs


    #红色 adv 防守方
    #绿色 good 进攻

