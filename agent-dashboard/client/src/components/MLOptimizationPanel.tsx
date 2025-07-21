import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Brain, Users, TrendingUp, Zap, Award, Network } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface MLOptimizationData {
  optimization: {
    agent_performance_scores: Record<string, { score: number; samples: number }>;
    decision_success_rates: Record<string, number>;
    pattern_library_size: Record<string, number>;
  };
  collaboration_insights: {
    collaboration_scores: Record<string, Record<string, number>>;
    agent_expertise: Record<string, string[]>;
    optimal_teams: Array<{
      task_type: string;
      optimal_team: string[];
      success_rate: number;
    }>;
    network_density: number;
  };
  context_status: {
    current_task: any;
    active_agents: number;
    task_count: number;
  };
}

const COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899'];

export const MLOptimizationPanel: React.FC = () => {
  const [data, setData] = useState<MLOptimizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [evolutionData, setEvolutionData] = useState<any>(null);

  useEffect(() => {
    fetchMLData();
    const interval = setInterval(fetchMLData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMLData = async () => {
    try {
      const response = await fetch('/api/jarvis/ml-optimization/dashboard');
      const mlData = await response.json();
      setData(mlData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch ML optimization data:', error);
      setLoading(false);
    }
  };

  const fetchAgentEvolution = async (agentId: string) => {
    try {
      const response = await fetch(`/api/jarvis/ml-optimization/agent-evolution/${agentId}?days=30`);
      const evolution = await response.json();
      setEvolutionData(evolution);
      setSelectedAgent(agentId);
    } catch (error) {
      console.error('Failed to fetch agent evolution:', error);
    }
  };

  const triggerLearningCycle = async () => {
    try {
      await fetch('/api/jarvis/ml-optimization/trigger-learning-cycle', { method: 'POST' });
      // Refresh data after learning cycle
      setTimeout(fetchMLData, 2000);
    } catch (error) {
      console.error('Failed to trigger learning cycle:', error);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading ML optimization data...</div>;
  }

  if (!data) {
    return <div className="text-red-500">Failed to load ML optimization data</div>;
  }

  // Prepare chart data
  const performanceData = Object.entries(data.optimization.agent_performance_scores)
    .map(([agent, { score, samples }]) => ({
      agent,
      score: (score * 100).toFixed(1),
      samples,
    }))
    .sort((a, b) => parseFloat(b.score) - parseFloat(a.score))
    .slice(0, 10);

  const decisionSuccessData = Object.entries(data.optimization.decision_success_rates)
    .map(([type, rate]) => ({
      type,
      successRate: (rate * 100).toFixed(1),
    }));

  const expertiseData = Object.entries(data.collaboration_insights.agent_expertise)
    .map(([agent, skills]) => ({
      agent,
      skills: skills.length,
      expertise: skills.join(', '),
    }))
    .slice(0, 8);

  const teamSuccessData = data.collaboration_insights.optimal_teams.map(team => ({
    taskType: team.task_type,
    successRate: (team.success_rate * 100).toFixed(1),
    teamSize: team.optimal_team.length,
  }));

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.context_status.active_agents}</div>
            <p className="text-xs text-muted-foreground">
              {Object.keys(data.optimization.agent_performance_scores).length} tracked
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Network Density</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(data.collaboration_insights.network_density * 100).toFixed(1)}%
            </div>
            <Progress value={data.collaboration_insights.network_density * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Performance</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(
                Object.values(data.optimization.agent_performance_scores).reduce(
                  (sum, { score }) => sum + score,
                  0
                ) / Object.keys(data.optimization.agent_performance_scores).length * 100
              ).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">Across all agents</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Learning Active</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <Badge variant="default" className="mb-2">Active</Badge>
            <Button 
              size="sm" 
              onClick={triggerLearningCycle}
              className="w-full"
              variant="outline"
            >
              <Zap className="h-3 w-3 mr-1" />
              Trigger Cycle
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="performance">Agent Performance</TabsTrigger>
          <TabsTrigger value="decisions">Decision Analytics</TabsTrigger>
          <TabsTrigger value="collaboration">Collaboration</TabsTrigger>
          <TabsTrigger value="evolution">Agent Evolution</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Agent Performance Scores</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="agent" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="score" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Agent Expertise Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={expertiseData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="agent" />
                  <PolarRadiusAxis />
                  <Radar
                    name="Skills Count"
                    dataKey="skills"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.6}
                  />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="decisions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Decision Success Rates by Type</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={decisionSuccessData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="type" type="category" width={120} />
                  <Tooltip />
                  <Bar dataKey="successRate" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pattern Library Size</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={Object.entries(data.optimization.pattern_library_size).map(
                      ([type, count]) => ({ name: type, value: count })
                    )}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {Object.entries(data.optimization.pattern_library_size).map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="collaboration" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Optimal Team Compositions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.collaboration_insights.optimal_teams.map((team, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-semibold capitalize">{team.task_type.replace('_', ' ')}</h4>
                      <Badge variant="outline">
                        {(team.success_rate * 100).toFixed(0)}% Success
                      </Badge>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {team.optimal_team.map((agent) => (
                        <Badge key={agent} variant="secondary">
                          {agent}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Team Success Rates by Task Type</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={teamSuccessData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="taskType" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="successRate" fill="#8b5cf6" name="Success Rate %" />
                  <Bar dataKey="teamSize" fill="#10b981" name="Team Size" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="evolution" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Select Agent to View Evolution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {Object.keys(data.optimization.agent_performance_scores).map((agent) => (
                  <Button
                    key={agent}
                    variant={selectedAgent === agent ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => fetchAgentEvolution(agent)}
                  >
                    {agent}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {evolutionData && (
            <Card>
              <CardHeader>
                <CardTitle>Evolution of {selectedAgent}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="text-center">
                    <Award className="h-8 w-8 mx-auto mb-2 text-yellow-500" />
                    <div className="text-2xl font-bold">
                      {(evolutionData.current_performance_score * 100).toFixed(1)}%
                    </div>
                    <p className="text-sm text-muted-foreground">Current Score</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {evolutionData.decision_metrics.total_decisions_involved}
                    </div>
                    <p className="text-sm text-muted-foreground">Decisions Involved</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {(evolutionData.decision_metrics.success_rate * 100).toFixed(1)}%
                    </div>
                    <p className="text-sm text-muted-foreground">Decision Success Rate</p>
                  </div>
                </div>

                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={evolutionData.task_history}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="completion_rate"
                      stroke="#8b5cf6"
                      name="Completion Rate"
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="tasks_handled"
                      stroke="#10b981"
                      name="Tasks Handled"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};