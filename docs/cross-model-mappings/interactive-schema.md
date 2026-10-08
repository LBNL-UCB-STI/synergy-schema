# Database Schema & Entity-Relationship Diagrams

This page presents the compiled Entity-Relationship (ER) diagrams and foreign key contracts linking the multi-model population, vehicle fleet, land-use, and network skim tables across **UrbanSim**, **DEMOS**, **ATLAS**, **POLARIS**, and **OMX Skims** for Deliverable #1.

All tables, column definitions, primary keys, foreign keys, and cross-model handoff relationships are **generated directly from the LinkML schema contracts** (`src/synergy_schema/schema/deliverable_1_static_schema.yaml`).

---

## 1. Core Population & Vehicle Fleet ERD

The diagram below isolates the synthetic agent tables across DEMOS, ATLAS, and POLARIS. Edges link directly between the corresponding key attributes:

- **Solid Blue Edges ($N:1$)**: Strict intra-model relational foreign keys (e.g., person-to-household membership, vehicle-to-household ownership).
- **Dashed Colored Edges ($1:1$ or $N:1$)**: Cross-model pipeline joins and translation lineages (e.g., ATLAS vehicle fleet assignment to DEMOS synthetic households, POLARIS demand database recoding).

<div class="erd-diagram-card">
  <p><a href="../assets/images/deliverable_1_population_erd.svg" target="_blank" class="md-button md-button--primary">Open High-Resolution Population ERD (Vector SVG)</a></p>
  <img src="../assets/images/deliverable_1_population_erd.svg" alt="Core Synthetic Population and Vehicle Fleet ER Diagram" class="erd-diagram-img" />
</div>

---

## 2. Complete 5-Model Regional Architecture ERD

The regional architecture diagram links all 12 tables across the 5 models, including UrbanSim Census Block marginals, Block-to-TAZ aggregation tables, and Open Matrix (`.omx`) travel impedance matrices.

<div class="erd-diagram-card">
  <p><a href="../assets/images/deliverable_1_erd.svg" target="_blank" class="md-button md-button--primary">Open High-Resolution Regional ERD (Vector SVG)</a></p>
  <img src="../assets/images/deliverable_1_erd.svg" alt="Complete 5-Model Regional Architecture ER Diagram" class="erd-diagram-img" />
</div>

---

## 3. Foreign Key & Pipeline Linkage Reference Table

The table below documents every intra-model foreign key and cross-model handoff contract compiled from the schema:

| Child Table | Child Column | Parent Table | Parent Column | Cardinality | Link Type | Pipeline Purpose |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `BlockToTazMapping` | `block_id` `[FK]` | `UrbanSimBlockMarginals` | `block_id` `[PK]` | $N:1$ | Intra-Model FK | Associates Census Blocks with regional marginal controls |
| `BlockToTazMapping` | `zone_id` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Intra-Model FK | Maps Census Blocks into POLARIS-compatible TAZ zones |
| `DemosPolarisMappedPerson` | `household` `[FK]` | `DemosPolarisMappedHousehold` | `household` `[PK]` | $N:1$ | Intra-Model FK | Enforces person membership in synthetic households |
| `AtlasVehicleFleetOutput` | `houseid` `[FK]` | `AtlasHouseholdFleetOutput` | `houseid` `[PK]` | $N:1$ | Intra-Model FK | Associates discrete vehicles with synthesized household fleets |
| `PolarisDemandDatabasePerson` | `household` `[FK]` | `PolarisDemandDatabaseHousehold` | `household` `[PK]` | $N:1$ | Intra-Model FK | Enforces POLARIS traveler membership in households |
| `PolarisDemandDatabaseVehicle` | `hhold` `[FK]` | `PolarisDemandDatabaseHousehold` | `household` `[PK]` | $N:1$ | Intra-Model FK | Associates POLARIS vehicles with households |
| `AtlasHouseholdFleetOutput` | `houseid` `[FK]` | `DemosPolarisMappedHousehold` | `household` `[PK]` | $1:1$ | Cross-Model Join | Joins ATLAS synthesized vehicle counts to DEMOS households |
| `PolarisDemandDatabaseHousehold` | `household` `[FK]` | `DemosPolarisMappedHousehold` | `household` `[PK]` | $1:1$ | Cross-Model Lineage | Lineage tracking from DEMOS base population to POLARIS demand |
| `PolarisDemandDatabaseVehicle` | `vehicle_id` `[FK]` | `AtlasVehicleFleetOutput` | `vehid` `[PK]` | $1:1$ | Cross-Model Lineage | Recodes ATLAS discrete vehicles to POLARIS vehicle types |
| `PolarisDemandDatabaseHousehold` | `location` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Assigns household residence to UrbanSim TAZ zones |
| `DemosPolarisMappedHousehold` | `block_id` `[FK]` | `UrbanSimBlockMarginals` | `block_id` `[PK]` | $N:1$ | Cross-Model Spatial | Controls demographic synthesis by Census Block marginals |
| `InputNetworkSkims` | `zone_count` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Confirms skim matrix dimensions match active TAZ zones |
| `NextYearNetworkSkims` | `zone_count` `[FK]` | `UrbanSimZonalTotals` | `zone_id` `[PK]` | $N:1$ | Cross-Model Spatial | Confirms iterative skim matrix dimensions match active TAZ zones |

---

## 4. Interactive Schema Inspector

The interactive canvas below provides dynamic filtering and metadata inspection for individual tables and columns:

<div class="schema-explorer-outer">
  <!-- Controls Bar -->
  <div class="schema-explorer-toolbar">
    <div class="schema-filter-group">
      <span class="schema-toolbar-label">Model:</span>
      <button class="schema-filter-btn active" data-model="ALL">All Models</button>
      <button class="schema-filter-btn" data-model="UrbanSim">UrbanSim</button>
      <button class="schema-filter-btn" data-model="DEMOS">DEMOS</button>
      <button class="schema-filter-btn" data-model="ATLAS">ATLAS</button>
      <button class="schema-filter-btn" data-model="POLARIS">POLARIS</button>
      <button class="schema-filter-btn" data-model="Skims">OMX Skims</button>
    </div>
    <div class="schema-actions-group">
      <div class="schema-search-box">
        <input type="text" id="schema-search-input" placeholder="Search tables or columns..." />
      </div>
      <div class="schema-zoom-controls">
        <button id="schema-zoom-in" title="Zoom In">+</button>
        <button id="schema-zoom-out" title="Zoom Out">&minus;</button>
        <button id="schema-zoom-fit" title="Fit to View">Fit View</button>
        <button id="schema-fullscreen" title="Toggle Fullscreen">&#x26F6;</button>
      </div>
    </div>
  </div>

  <!-- Main Viewport -->
  <div id="schema-viewport" class="schema-viewport">
    <svg id="schema-svg-layer" class="schema-svg-layer"></svg>
    <div id="schema-nodes-layer" class="schema-nodes-layer"></div>

    <!-- Inspector Drawer -->
    <div id="schema-inspector" class="schema-inspector hidden">
      <div class="schema-inspector-header">
        <div class="schema-inspector-title-wrap">
          <span id="inspector-model-badge" class="schema-model-badge">MODEL</span>
          <h3 id="inspector-table-name">Table Name</h3>
        </div>
        <button id="inspector-close-btn" class="schema-close-btn">&times;</button>
      </div>
      <div class="schema-inspector-body">
        <p id="inspector-description" class="schema-inspector-desc"></p>

        <h4>Relationships</h4>
        <div id="inspector-relationships" class="schema-relationships-list"></div>

        <h4>Columns & Field Types</h4>
        <div id="inspector-columns-table-wrap">
          <table class="schema-inspector-table">
            <thead>
              <tr>
                <th>Column</th>
                <th>Type</th>
                <th>Key</th>
              </tr>
            </thead>
            <tbody id="inspector-columns-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>
