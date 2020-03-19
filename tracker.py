import sys
import numpy  #1.16.3
from scipy.optimize import linear_sum_assignment #1.3.0

class Fish:

    def __init__(self, fishId, contour ,centroid, size, diameter):
        self.id = fishId
        self.contour = contour
        self.centroid = centroid
        self.size = size
        self.distanceTravelled = 0
        self.speed = 0
        self.diameter = diameter

class MinimumSpanningTree:

    def __init__(self, graph):
        self.graph = graph
        self.visited = []

    def Update(self):
        
        weight = 0
        minimumKey = 0
        for i in range(len(self.graph)-1):
            self.visited.append(minimumKey)
            minimumCost = sys.float_info.max
            for vertice in self.visited:
                adjVertexs = self.graph.get(vertice, 0)
                for key, value in adjVertexs.items():
                    if not key in self.visited:
                        if value < minimumCost:
                            minimumKey = key
                            minimumCost = value
            # self.weight += minimumCost
            weight += minimumCost
        
        return weight

class Tracker:

    def __init__(self):
        self.fishes = []
        self.cluster = 0
        self.diameter_ratio = 1
        self.area_ratio = 1

    def UpdateAreaRatio(self, ratio):
        self.area_ratio = ratio

    def UpdateDiameterRatio(self, ratio):
        self.diameter_ratio = ratio

    def Update(self, centroids, timeElapsed):

        # assign fish via hungarian algorithm

        if (len(self.fishes) == 0):
            count = 0
            for i in range(len(centroids)):
                fish = Fish(count, centroids[i][0], centroids[i][1], centroids[i][2], centroids[i][3])
                self.fishes.append(fish)
                count += 1

        N = len(self.fishes)
        M = len(centroids)
        cost = numpy.zeros(shape=(N,M)) # cost matrix
        
        for i in range(len(self.fishes)):
            for j in range(len(centroids)):
                v1 = self.fishes[i].centroid
                v2 = centroids[j][1]
                distance = numpy.sqrt(((v2[0]-v1[0])**2) + ((v2[1]-v1[1])**2))
                cost[i][j] = int(distance)
        
        assignment = []
        for _ in range(N):
            assignment.append(-1)

        row_index, col_index = linear_sum_assignment(cost)

        for i in range(len(row_index)):
            assignment[row_index[i]] = col_index[i]

        for i in range(len(assignment)):
            if not assignment[i] == -1:
                self.fishes[i].contour = centroids[assignment[i]][0]
                self.fishes[i].centroid = centroids[assignment[i]][1]
                self.fishes[i].size = centroids[assignment[i]][2]
                self.fishes[i].distanceTravelled += cost[i][assignment[i]]
                if not timeElapsed == 0:
                    self.fishes[i].speed = self.fishes[i].distanceTravelled/timeElapsed

        # clustering average / mst weight

        graph = {}

        for fish in self.fishes:
            adjList = {}
            for adjFish in self.fishes:
                if not adjFish.id == fish.id:
                    v1 = fish.centroid
                    v2 = adjFish.centroid
                    distance = numpy.sqrt(((v2[0]-v1[0])**2) + ((v2[1]-v1[1])**2))
                    adjList.update({adjFish.id: distance})
            graph.update({fish.id: adjList})

        mst = MinimumSpanningTree(graph)
        self.cluster = mst.Update()