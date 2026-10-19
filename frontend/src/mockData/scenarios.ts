export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  mode: 'NORMAL' | 'DISASTER';
  primaryRole: 'COORDINATOR' | 'FOOD_PROVIDER' | 'RECIPIENT' | 'VOLUNTEER';
  featuredInsightId?: string;
  featuredTaskId?: string;
}

export const mockScenarios: DemoScenario[] = [
  {
    id: 'SCENARIO-01',
    name: 'Normal Operations: Evening Hot Meal Rescue',
    description: 'GreenBites Bistro lists 50 kg surplus dinner; AI matches with Hope Foundation Shelter; Volunteer Dinesh accepts delivery.',
    mode: 'NORMAL',
    primaryRole: 'FOOD_PROVIDER',
    featuredInsightId: 'AI-001',
    featuredTaskId: 'TASK-301',
  },
  {
    id: 'SCENARIO-02',
    name: 'Disaster Mode: Lunawa Lagoon Flood Response',
    description: 'Monsoon flash flood declared; Coordinator mobilizes relief water supplies and high-capacity vans to Lunawa camp.',
    mode: 'DISASTER',
    primaryRole: 'COORDINATOR',
    featuredInsightId: 'AI-003',
    featuredTaskId: 'TASK-303',
  },
  {
    id: 'SCENARIO-03',
    name: 'Volunteer Mobility: Disrupted Route Reroute',
    description: 'Volunteer encounters flooded road culvert; platform alerts coordinator and triggers safe alternative waypoint.',
    mode: 'NORMAL',
    primaryRole: 'VOLUNTEER',
    featuredInsightId: 'AI-005',
    featuredTaskId: 'TASK-305',
  },
];
