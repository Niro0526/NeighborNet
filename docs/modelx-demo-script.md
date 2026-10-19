# NeighborNet AI — ModelX 2.0 Competition Demonstration Script & Plan (Phase 5)

## 1. Executive Summary & Value Proposition

**Team**: Aivura
**Project**: NeighborNet AI
**Track**: ModelX 2.0 Hackathon Competition
**Core Innovation**: A dual-mode (Normal Community Food Rescue & Rapid Disaster Relief) resource matching platform powered by Google OR-Tools CP-SAT constraint programming, geospatial PostGIS routing, and real-time courier reassignment.

---

## 2. Demo Environment Setup (Reproducible & Idempotent)

To prepare the clean live demonstration environment:

```bash
# 1. Ensure PostgreSQL is running
# 2. Reset and seed demo database (in development mode with DEBUG=True)
python backend/manage.py seed_demo --force

# 3. Start backend development server
python backend/manage.py runserver 8000

# 4. In a separate terminal, launch the frontend
cd frontend
npm run dev
```

Open `http://localhost:5173` in your browser. All 7 demo personas are seeded and operational in the live PostgreSQL database.

---

## 3. The 3-Minute Pitch & Live Demo Plan

| Time | Segment | On-Screen Action | Presenter Talking Points |
|---|---|---|---|
| **0:00 - 0:35** | **Problem & Context** | Home page & Sri Lanka evidence map | *"Every evening across Colombo and Moratuwa, hundreds of kilograms of fresh cooked food and produce are discarded by commercial kitchens, while local community shelters face acute nutritional deficits. When monsoon flash floods hit, this distribution gap turns into a life-or-death logistics crisis."* |
| **0:35 - 1:15** | **Surplus Listing & NGO Demand** | Provider portal & Recipient request | *"Watch this live: Cinnamon Grand Kitchen registers 25 kg of fresh cooked rice and curry with a 4-hour shelf-life limit. Simultaneously, Sarvodaya Community Center logs an urgent demand for 20 kg."* |
| **1:15 - 1:55** | **OR-Tools Solver & Coordinator Approval** | Admin Workspace -> Recommendation Batch | *"Instead of crude first-come-first-served queues, our Google OR-Tools CP-SAT solver optimizes globally: factoring shelf-life decay, vehicle capacity, and spatial distance. The coordinator reviews the mathematical match with 0 constraint violations and clicks 'Approve Batch'."* |
| **1:55 - 2:30** | **Volunteer Courier Execution** | Volunteer Dashboard -> Claim & Deliver | *"Our verified motorcycle volunteer courier receives the dispatch, accepts the route, picks up the insulated thermal box, and marks it delivered with real-time GPS verification."* |
| **2:30 - 3:00** | **Disaster Mode & Impact Evidence** | Header toggle -> Disaster Mode | *"When disaster strikes, one click activates Emergency Disaster Mode, reprioritizing the entire solver toward potable water and emergency dry rations. NeighborNet AI turns surplus into community resilience."* |

---

## 4. The 5-Minute Comprehensive Demo Plan

| Time | Demo Phase | Persona / Role | Live Action & Key Highlights |
|---|---|---|---|
| **0:00 - 0:45** | **The Crisis & Real Sri Lankan Evidence** | Public / Overview | Show HARTI vegetable wholesale bulletin and Kelani River flood reports. Explain that benchmark heuristics derive from authentic Sri Lankan public data. |
| **0:45 - 1:30** | **Normal Mode: Provider & Recipient Flow** | Food Provider (`provider@neighbornet.org`) -> Recipient (`recipient@neighbornet.org`) | Provider posts surplus cooked meal batch. Recipient creates nutritional request. Highlight dietary constraints (Halal, Vegetarian). |
| **1:30 - 2:30** | **Mathematical Optimization Engine** | Coordinator (`admin@neighbornet.org`) | Open Coordinator Workspace. Trigger OR-Tools CP-SAT solver. Show mathematical score breakdown, objective function values, and one-click atomic approval. |
| **2:30 - 3:15** | **Volunteer Dispatch & PostGIS Tracking** | Volunteer Courier (`volunteer@neighbornet.org`) | Courier accepts task. View map route with distance calculation. Advance states: `ASSIGNED` -> `PICKED_UP` -> `DELIVERED`. |
| **3:15 - 4:15** | **Disaster Mode Activation & Recovery** | Coordinator & Emergency Shelter | Coordinator switches platform to **Disaster Response Mode**. Demonstrate how algorithm pivots objective weights from shelf-life minimization to life-survival priority. Demonstrate courier vehicle disruption and instant alternative courier recovery recommendation. |
| **4:15 - 5:00** | **Advanced Benchmark Validation & Q&A** | Analytics / Benchmark Dashboard | Display Phase 4.6 evaluation metrics across 7 operational scenarios (96.8% demand fulfillment, 0 constraint violations). Close with production-readiness summary. |

---

## 5. Technical Explanation: Google OR-Tools CP-SAT Solver

NeighborNet AI models resource matching as a **Multi-Objective Mixed-Integer Constraint Satisfaction Problem (CP-SAT)**:

### Decision Variables:
$$x_{i,j,v} \in \{0, 1\}$$
Binary assignment indicating whether surplus food listing $i$ is allocated to recipient request $j$ transported by volunteer courier $v$.

### Hard Constraints:
1. **Supply Capacity**: Total quantity allocated from listing $i$ cannot exceed available stock $S_i$.
2. **Demand Fulfillment**: Total quantity delivered to recipient $j$ cannot exceed requested quota $D_j$.
3. **Vehicle Capacity**: Carried load cannot exceed volunteer vehicle payload limit $C_v$ (e.g. 15 kg for backpack, 35 kg for motorcycle, 300 kg for van).
4. **Shelf-Life Horizon**: Estimated travel time $T_{i,j,v}$ must strictly be less than remaining safe shelf-life $E_i$.
5. **Dietary & Handling Compliance**: Halal/Vegetarian and cold-chain/thermal-box constraints must be satisfied strictly ($x_{i,j,v} = 0$ if incompatible).

### Objective Function:
$$\max \sum_{i,j,v} x_{i,j,v} \cdot \left( w_1 \cdot \text{Urgency}_j + w_2 \cdot (1 - \text{Decay}_i) - w_3 \cdot \text{Distance}_{i,j} + w_4 \cdot \text{Equity}_j \right)$$

In **Disaster Mode**, $w_1$ (Urgency) and $w_4$ (Survival Needs) are multiplied by $5\times$, prioritizing life-saving sustenance over travel efficiency.

---

## 6. Screenshots Checklist for Submission Slides

1. [ ] **Public Evidence Map**: Colombo & Kelani River basin hazard mapping with HARTI market indices.
2. [ ] **Provider Surplus Form**: Food listing with shelf-life countdown and storage requirements.
3. [ ] **Recipient Request Form**: NGO dietary requirements and urgency flag.
4. [ ] **Coordinator Intelligence Workspace**: OR-Tools solver recommendation batch with constraint metrics.
5. [ ] **Volunteer Courier Interface**: Active delivery route, pickup instructions, and proof of delivery.
6. [ ] **Disaster Emergency Mode**: Red-themed emergency interface with disaster priority banners.
7. [ ] **Recovery Plan Visualizer**: Disrupted route and alternative courier reassignment.
8. [ ] **Advanced Benchmark Matrix**: 7-scenario evaluation graph showing demand fulfillment and solver efficiency.

---

## 7. Known Limitations & Next Steps

1. **Traffic Congestion API**: Currently utilizes PostGIS spheroidal distance matrices; production deployment will incorporate live OpenStreetMap / OSRM routing with real-time Sri Lankan road congestion.
2. **Offline SMS Dispatch**: In remote disaster zones with degraded cellular data, SMS-based volunteer dispatch fallback will be implemented.
3. **Cold-Chain IoT Telemetry**: Direct Bluetooth/cellular integration with IoT temperature probes inside volunteer thermal boxes.

---

## 8. Data Attribution & Synthetic Scenario Disclaimer

> **Transparency Notice**:
> All baseline geographical boundaries, price indices, and flood inundation zones are derived from genuine public Sri Lankan sources (HARTI Sri Lanka, DMC, and Department of Census and Statistics).
> All specific food listings, volunteer courier identities, and operational test transactions are synthetic demonstration records generated to safely prove mathematical and platform capability without exposing personal citizen information.
