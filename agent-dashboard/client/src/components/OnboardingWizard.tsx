import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  CheckCircle2,
  Circle,
  Rocket,
  Users,
  Brain,
  Zap,
  ArrowRight,
  PlayCircle,
  FileText,
  Sparkles,
  X,
} from 'lucide-react';
import confetti from 'canvas-confetti';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  action?: () => void;
  completed: boolean;
}

export const OnboardingWizard: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState<OnboardingStep[]>([
    {
      id: 'welcome',
      title: 'Welcome to Jarvis!',
      description: 'Your AI agent team is ready to help you build amazing things.',
      completed: false,
    },
    {
      id: 'meet-agents',
      title: 'Meet Your AI Agents',
      description: 'You have 5 specialized agents working for you.',
      completed: false,
    },
    {
      id: 'first-task',
      title: 'Create Your First Task',
      description: 'Let\'s give the agents something to work on.',
      completed: false,
    },
    {
      id: 'explore-ml',
      title: 'Explore ML Insights',
      description: 'See how your agents learn and improve over time.',
      completed: false,
    },
    {
      id: 'complete',
      title: 'You\'re All Set!',
      description: 'Your Jarvis system is ready for action.',
      completed: false,
    },
  ]);

  const [taskInput, setTaskInput] = useState('');
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    // Check if user is new (first time)
    const hasSeenOnboarding = localStorage.getItem('jarvis_onboarding_completed');
    if (!hasSeenOnboarding) {
      setIsOpen(true);
    }
  }, []);

  const completeStep = (stepId: string) => {
    setSteps(steps.map(step => 
      step.id === stepId ? { ...step, completed: true } : step
    ));
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      completeStep(steps[currentStep].id);
      setCurrentStep(currentStep + 1);
    } else {
      // Complete onboarding
      completeOnboarding();
    }
  };

  const handleSkip = () => {
    setIsOpen(false);
    localStorage.setItem('jarvis_onboarding_completed', 'true');
  };

  const completeOnboarding = () => {
    localStorage.setItem('jarvis_onboarding_completed', 'true');
    setShowConfetti(true);
    
    // Fire confetti
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });

    setTimeout(() => {
      setIsOpen(false);
    }, 3000);
  };

  const createFirstTask = async () => {
    if (!taskInput.trim()) return;

    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: taskInput,
          project_id: 'project-001',
        }),
      });

      if (response.ok) {
        completeStep('first-task');
        setTaskInput('');
      }
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  const getStepContent = () => {
    const step = steps[currentStep];

    switch (step.id) {
      case 'welcome':
        return (
          <div className="text-center space-y-6">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", duration: 0.8 }}
            >
              <Rocket className="w-24 h-24 mx-auto text-blue-500" />
            </motion.div>
            <h2 className="text-3xl font-bold">Welcome to Jarvis! 🎉</h2>
            <p className="text-lg text-gray-600">
              Your personal AI development team is ready to help you build amazing projects.
              Let's take a quick tour to get you started.
            </p>
            <div className="grid grid-cols-2 gap-4 mt-8">
              <Card className="border-2 border-blue-200 bg-blue-50">
                <CardContent className="pt-6">
                  <Users className="w-8 h-8 text-blue-600 mb-2" />
                  <h3 className="font-semibold">5 AI Agents</h3>
                  <p className="text-sm text-gray-600">Ready to work</p>
                </CardContent>
              </Card>
              <Card className="border-2 border-green-200 bg-green-50">
                <CardContent className="pt-6">
                  <Brain className="w-8 h-8 text-green-600 mb-2" />
                  <h3 className="font-semibold">ML Optimization</h3>
                  <p className="text-sm text-gray-600">Always learning</p>
                </CardContent>
              </Card>
            </div>
          </div>
        );

      case 'meet-agents':
        return (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-center mb-6">Meet Your AI Team</h2>
            <div className="space-y-3">
              {[
                { name: 'Orchestrator', role: 'Team Leader', icon: '🧠', color: 'purple' },
                { name: 'Architect', role: 'System Designer', icon: '🏗️', color: 'blue' },
                { name: 'Researcher', role: 'Information Expert', icon: '🔬', color: 'green' },
                { name: 'Quality', role: 'Code Reviewer', icon: '✅', color: 'yellow' },
                { name: 'Communicator', role: 'Status Reporter', icon: '📢', color: 'pink' },
              ].map((agent, index) => (
                <motion.div
                  key={agent.name}
                  initial={{ x: -50, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className={`border-2 border-${agent.color}-200 hover:shadow-lg transition-shadow`}>
                    <CardContent className="flex items-center space-x-4 p-4">
                      <div className="text-3xl">{agent.icon}</div>
                      <div className="flex-1">
                        <h3 className="font-semibold">{agent.name}</h3>
                        <p className="text-sm text-gray-600">{agent.role}</p>
                      </div>
                      <Badge variant="outline" className={`border-${agent.color}-500`}>
                        Online
                      </Badge>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        );

      case 'first-task':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <FileText className="w-16 h-16 mx-auto text-green-500 mb-4" />
              <h2 className="text-2xl font-bold">Create Your First Task</h2>
              <p className="text-gray-600 mt-2">
                Give your agents something to work on. They'll collaborate to complete it!
              </p>
            </div>
            <div className="space-y-4">
              <Input
                placeholder="e.g., Create a REST API for user management"
                value={taskInput}
                onChange={(e) => setTaskInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && createFirstTask()}
                className="text-lg p-6"
              />
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  onClick={() => setTaskInput('Build a simple web application')}
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Web App
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setTaskInput('Create a REST API with authentication')}
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  REST API
                </Button>
              </div>
              <Button
                onClick={createFirstTask}
                disabled={!taskInput.trim()}
                className="w-full"
                size="lg"
              >
                <PlayCircle className="w-5 h-5 mr-2" />
                Create Task
              </Button>
            </div>
          </div>
        );

      case 'explore-ml':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <Brain className="w-16 h-16 mx-auto text-purple-500 mb-4" />
              <h2 className="text-2xl font-bold">ML Optimization Active</h2>
              <p className="text-gray-600 mt-2">
                Your agents are learning from every task and getting smarter!
              </p>
            </div>
            <div className="space-y-4">
              <Card className="border-2 border-purple-200 bg-purple-50">
                <CardContent className="p-6">
                  <h3 className="font-semibold mb-2">What's happening:</h3>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center">
                      <CheckCircle2 className="w-4 h-4 text-green-500 mr-2" />
                      Agents analyze task outcomes
                    </li>
                    <li className="flex items-center">
                      <CheckCircle2 className="w-4 h-4 text-green-500 mr-2" />
                      Successful patterns are identified
                    </li>
                    <li className="flex items-center">
                      <CheckCircle2 className="w-4 h-4 text-green-500 mr-2" />
                      Performance improves over time
                    </li>
                    <li className="flex items-center">
                      <CheckCircle2 className="w-4 h-4 text-green-500 mr-2" />
                      Optimal teams are discovered
                    </li>
                  </ul>
                </CardContent>
              </Card>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => window.location.hash = '#/ml-optimization'}
              >
                <Zap className="w-4 h-4 mr-2" />
                View ML Dashboard
              </Button>
            </div>
          </div>
        );

      case 'complete':
        return (
          <div className="text-center space-y-6">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", duration: 0.8 }}
            >
              <CheckCircle2 className="w-24 h-24 mx-auto text-green-500" />
            </motion.div>
            <h2 className="text-3xl font-bold">You're All Set! 🚀</h2>
            <p className="text-lg text-gray-600">
              Your Jarvis system is ready. The agents are standing by to help you build amazing things!
            </p>
            <div className="bg-gray-100 rounded-lg p-6 text-left">
              <h3 className="font-semibold mb-3">Quick Tips:</h3>
              <ul className="space-y-2 text-sm">
                <li>• Press <kbd className="px-2 py-1 bg-white rounded">?</kbd> for keyboard shortcuts</li>
                <li>• Drag and drop files to create bulk tasks</li>
                <li>• Check ML Optimization daily to see improvements</li>
                <li>• Join our Discord community for help</li>
              </ul>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold">Getting Started with Jarvis</h1>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleSkip}
                className="text-white hover:bg-white/20"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
            <Progress
              value={((currentStep + 1) / steps.length) * 100}
              className="mt-4 h-2"
            />
          </div>

          {/* Content */}
          <div className="p-8 min-h-[400px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ x: 20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -20, opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                {getStepContent()}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-8 py-4 flex justify-between items-center">
            <div className="flex space-x-2">
              {steps.map((step, index) => (
                <div
                  key={step.id}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index <= currentStep ? 'bg-blue-500' : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
            <div className="flex space-x-3">
              {currentStep > 0 && currentStep < steps.length - 1 && (
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(currentStep - 1)}
                >
                  Back
                </Button>
              )}
              <Button onClick={handleNext}>
                {currentStep === steps.length - 1 ? (
                  <>
                    Get Started
                    <Rocket className="w-4 h-4 ml-2" />
                  </>
                ) : (
                  <>
                    Next
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};