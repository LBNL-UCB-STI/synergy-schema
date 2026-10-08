/**
 * Interactive Cross-Model Population Schema Explorer
 * Compiled directly from LinkML schema definitions.
 */

(function () {
  function initSchemaExplorer() {
    const data = window.SCHEMA_GRAPH_DATA;
    if (!data || !data.tables) return;

    const viewport = document.getElementById("schema-viewport");
    const svgLayer = document.getElementById("schema-svg-layer");
    const nodesLayer = document.getElementById("schema-nodes-layer");
    const inspector = document.getElementById("schema-inspector");
    const searchInput = document.getElementById("schema-search-input");
    const filterBtns = document.querySelectorAll(".schema-filter-btn");

    if (!viewport || !svgLayer || !nodesLayer) return;

    let scale = 0.75;
    let panX = 40;
    let panY = 20;
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    let activeModelFilter = "ALL";
    let selectedTableId = null;

    // Node elements and bounding box cache
    const tableNodes = new Map();
    const tableBounds = new Map();

    // 1. Render Table Nodes
    nodesLayer.innerHTML = "";
    data.tables.forEach((table) => {
      const node = document.createElement("div");
      node.className = "schema-table-card";
      node.id = `table-${table.id}`;
      node.dataset.tableId = table.id;
      node.dataset.model = table.model;
      node.style.left = `${table.x}px`;
      node.style.top = `${table.y}px`;
      node.style.width = `${table.width}px`;

      const modelMeta = data.models[table.model] || { color: "#64748b", badge: table.model };

      // Header
      const header = document.createElement("div");
      header.className = "table-card-header";
      header.style.borderTopColor = modelMeta.color;

      const titleWrap = document.createElement("div");
      const modelBadge = document.createElement("span");
      modelBadge.className = "table-card-badge";
      modelBadge.style.backgroundColor = modelMeta.color;
      modelBadge.textContent = modelMeta.badge;

      const title = document.createElement("h4");
      title.className = "table-card-title";
      title.textContent = table.name;
      titleWrap.appendChild(modelBadge);
      titleWrap.appendChild(title);

      header.appendChild(titleWrap);
      node.appendChild(header);

      // Columns Body
      const colsList = document.createElement("div");
      colsList.className = "table-card-columns";

      // Show first 6 columns by default, with "... more" if needed
      const maxDisplayCols = 7;
      const displayCols = table.columns.slice(0, maxDisplayCols);

      displayCols.forEach((col) => {
        const row = document.createElement("div");
        row.className = "table-card-col-row";

        const colLeft = document.createElement("div");
        colLeft.className = "col-left";

        if (col.pk) {
          const pk = document.createElement("span");
          pk.className = "card-badge pk-badge";
          pk.textContent = "PK";
          colLeft.appendChild(pk);
        } else if (col.fk) {
          const fk = document.createElement("span");
          fk.className = "card-badge fk-badge";
          fk.textContent = "FK";
          colLeft.appendChild(fk);
        } else if (col.crosswalk) {
          const cw = document.createElement("span");
          cw.className = "card-badge cw-badge";
          cw.textContent = col.crosswalk;
          colLeft.appendChild(cw);
        }

        const colName = document.createElement("span");
        colName.className = "col-name";
        colName.textContent = col.name;
        colLeft.appendChild(colName);

        const colType = document.createElement("span");
        colType.className = "col-type";
        colType.textContent = col.type;

        row.appendChild(colLeft);
        row.appendChild(colType);
        colsList.appendChild(row);
      });

      if (table.columns.length > maxDisplayCols) {
        const moreRow = document.createElement("div");
        moreRow.className = "table-card-col-row more-row";
        moreRow.textContent = `+ ${table.columns.length - maxDisplayCols} more columns...`;
        colsList.appendChild(moreRow);
      }

      node.appendChild(colsList);

      // Footer / Inspect Button
      const footer = document.createElement("div");
      footer.className = "table-card-footer";
      const inspectBtn = document.createElement("button");
      inspectBtn.className = "table-inspect-btn";
      inspectBtn.textContent = "Inspect & Trace";
      inspectBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        selectTable(table.id);
      });
      footer.appendChild(inspectBtn);
      node.appendChild(footer);

      node.addEventListener("click", () => {
        selectTable(table.id);
      });

      nodesLayer.appendChild(node);
      tableNodes.set(table.id, node);
    });

    // 2. Render SVG Connections
    function renderEdges() {
      // Clear existing paths & markers
      svgLayer.innerHTML = `
        <defs>
          <marker id="arrow-solid" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#94a3b8"></path>
          </marker>
          <marker id="arrow-channel" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981"></path>
          </marker>
        </defs>
      `;

      data.edges.forEach((edge) => {
        const srcTable = data.tables.find((t) => t.id === edge.source);
        const tgtTable = data.tables.find((t) => t.id === edge.target);
        if (!srcTable || !tgtTable) return;

        // Skip if either table is filtered out
        if (activeModelFilter !== "ALL") {
          if (srcTable.model !== activeModelFilter && tgtTable.model !== activeModelFilter) {
            return;
          }
        }

        // Connection coordinates
        const isRightward = tgtTable.x > srcTable.x;
        const x1 = isRightward ? srcTable.x + srcTable.width : srcTable.x;
        const y1 = srcTable.y + 70;
        const x2 = isRightward ? tgtTable.x : tgtTable.x + tgtTable.width;
        const y2 = tgtTable.y + 70;

        const dx = Math.abs(x2 - x1) * 0.45;
        const cp1x = isRightward ? x1 + dx : x1 - dx;
        const cp2x = isRightward ? x2 - dx : x2 + dx;

        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        const d = `M ${x1} ${y1} C ${cp1x} ${y1}, ${cp2x} ${y2}, ${x2} ${y2}`;
        path.setAttribute("d", d);
        path.setAttribute("class", `schema-edge ${edge.dashed ? "dashed-edge" : "solid-edge"}`);
        path.setAttribute("stroke", edge.color || "#64748b");
        path.setAttribute("fill", "none");
        path.dataset.edgeId = edge.id;
        path.dataset.source = edge.source;
        path.dataset.target = edge.target;

        // Interaction highlighting
        if (selectedTableId) {
          if (edge.source === selectedTableId || edge.target === selectedTableId) {
            path.classList.add("highlighted");
            path.setAttribute("stroke-width", "3.5");
          } else {
            path.classList.add("dimmed");
          }
        }

        svgLayer.appendChild(path);
      });
    }

    // 3. Transform Application
    function updateTransform() {
      const transformStr = `translate(${panX}px, ${panY}px) scale(${scale})`;
      nodesLayer.style.transform = transformStr;
      svgLayer.style.transform = transformStr;
      renderEdges();
    }

    // 4. Table Selection & Inspector Drawer
    function selectTable(tableId) {
      if (selectedTableId === tableId) {
        // Toggle off
        selectedTableId = null;
        inspector.classList.add("hidden");
        tableNodes.forEach((node) => {
          node.classList.remove("selected", "highlighted", "dimmed");
        });
        updateTransform();
        return;
      }

      selectedTableId = tableId;
      const table = data.tables.find((t) => t.id === tableId);
      if (!table) return;

      // Update node styles
      const connectedTableIds = new Set([tableId]);
      data.edges.forEach((e) => {
        if (e.source === tableId) connectedTableIds.add(e.target);
        if (e.target === tableId) connectedTableIds.add(e.source);
      });

      tableNodes.forEach((node, id) => {
        node.classList.remove("selected", "highlighted", "dimmed");
        if (id === tableId) {
          node.classList.add("selected");
        } else if (connectedTableIds.has(id)) {
          node.classList.add("highlighted");
        } else {
          node.classList.add("dimmed");
        }
      });

      // Populate Inspector
      const modelMeta = data.models[table.model] || { color: "#64748b", badge: table.model };
      document.getElementById("inspector-model-badge").style.backgroundColor = modelMeta.color;
      document.getElementById("inspector-model-badge").textContent = modelMeta.badge;
      document.getElementById("inspector-table-name").textContent = `${table.name} (${table.alias})`;
      document.getElementById("inspector-description").textContent = table.description || "No description declared.";

      // Relationships in Inspector
      const relList = document.getElementById("inspector-relationships");
      relList.innerHTML = "";
      const relatedEdges = data.edges.filter((e) => e.source === tableId || e.target === tableId);

      if (relatedEdges.length === 0) {
        relList.innerHTML = `<span class="empty-state">No direct foreign keys or channels recorded.</span>`;
      } else {
        relatedEdges.forEach((e) => {
          const item = document.createElement("div");
          item.className = "inspector-rel-item";
          const isOutgoing = e.source === tableId;
          const targetName = isOutgoing ? e.target : e.source;
          const arrowSymbol = isOutgoing ? "&rarr;" : "&larr;";
          item.innerHTML = `
            <span class="rel-channel" style="color: ${e.color}">${e.label || e.id}</span>
            <span class="rel-arrow">${arrowSymbol}</span>
            <span class="rel-target">${targetName}</span>
          `;
          item.addEventListener("click", () => selectTable(targetName));
          relList.appendChild(item);
        });
      }

      // Columns Table in Inspector
      const colsBody = document.getElementById("inspector-columns-body");
      colsBody.innerHTML = "";
      table.columns.forEach((c) => {
        const tr = document.createElement("tr");

        let badgeHtml = "";
        if (c.pk) badgeHtml += `<span class="card-badge pk-badge">PK</span> `;
        if (c.fk) badgeHtml += `<span class="card-badge fk-badge">FK &rarr; ${c.fk}</span> `;
        if (c.crosswalk) badgeHtml += `<span class="card-badge cw-badge">${c.crosswalk}</span>`;

        tr.innerHTML = `
          <td><code>${c.name}</code></td>
          <td><span class="type-tag">${c.type}</span></td>
          <td>${badgeHtml || "<span class='text-muted'>&mdash;</span>"}</td>
          <td class="col-desc-text">${c.description || "<span class='text-muted'>&mdash;</span>"}</td>
        `;
        colsBody.appendChild(tr);
      });

      inspector.classList.remove("hidden");
      updateTransform();
    }

    // Close Inspector button
    document.getElementById("inspector-close-btn").addEventListener("click", () => {
      selectedTableId = null;
      inspector.classList.add("hidden");
      tableNodes.forEach((node) => {
        node.classList.remove("selected", "highlighted", "dimmed");
      });
      updateTransform();
    });

    // 5. Canvas Mouse & Touch Events (Pan & Zoom)
    viewport.addEventListener("mousedown", (e) => {
      if (e.target.closest(".schema-table-card") || e.target.closest(".schema-inspector")) {
        return;
      }
      isDragging = true;
      dragStartX = e.clientX - panX;
      dragStartY = e.clientY - panY;
      viewport.style.cursor = "grabbing";
    });

    window.addEventListener("mousemove", (e) => {
      if (!isDragging) return;
      panX = e.clientX - dragStartX;
      panY = e.clientY - dragStartY;
      updateTransform();
    });

    window.addEventListener("mouseup", () => {
      if (isDragging) {
        isDragging = false;
        viewport.style.cursor = "grab";
      }
    });

    viewport.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = 1.1;
      const rect = viewport.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const prevScale = scale;
      if (e.deltaY < 0) {
        scale = Math.min(scale * zoomFactor, 2.0);
      } else {
        scale = Math.max(scale / zoomFactor, 0.25);
      }

      // Anchor zoom to mouse pointer
      panX = mouseX - (mouseX - panX) * (scale / prevScale);
      panY = mouseY - (mouseY - panY) * (scale / prevScale);

      updateTransform();
    }, { passive: false });

    // 6. Controls Bar Buttons
    document.getElementById("schema-zoom-in").addEventListener("click", () => {
      scale = Math.min(scale * 1.2, 2.0);
      updateTransform();
    });

    document.getElementById("schema-zoom-out").addEventListener("click", () => {
      scale = Math.max(scale / 1.2, 0.25);
      updateTransform();
    });

    document.getElementById("schema-zoom-fit").addEventListener("click", () => {
      scale = 0.65;
      panX = 30;
      panY = 20;
      updateTransform();
    });

    const fullscreenBtn = document.getElementById("schema-fullscreen");
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener("click", () => {
        const outer = document.querySelector(".schema-explorer-outer");
        if (!document.fullscreenElement) {
          outer.requestFullscreen().catch((err) => console.error(err));
        } else {
          document.exitFullscreen().catch((err) => console.error(err));
        }
      });
    }

    // 7. Search & Filter
    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      tableNodes.forEach((node, tableId) => {
        const table = data.tables.find((t) => t.id === tableId);
        if (!table) return;

        if (!q) {
          node.classList.remove("search-match", "dimmed");
          return;
        }

        const matchesTable = table.name.toLowerCase().includes(q) || table.alias.toLowerCase().includes(q);
        const matchesCol = table.columns.some((c) => c.name.toLowerCase().includes(q));

        if (matchesTable || matchesCol) {
          node.classList.add("search-match");
          node.classList.remove("dimmed");
        } else {
          node.classList.remove("search-match");
          node.classList.add("dimmed");
        }
      });
    });

    filterBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        filterBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        activeModelFilter = btn.dataset.model;

        tableNodes.forEach((node, tableId) => {
          const table = data.tables.find((t) => t.id === tableId);
          if (!table) return;

          if (activeModelFilter === "ALL" || table.model === activeModelFilter) {
            node.style.display = "flex";
          } else {
            node.style.display = "none";
          }
        });

        renderEdges();
      });
    });

    // Initial setup
    updateTransform();
  }

  // Initialize once DOM is ready or after MkDocs navigation
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSchemaExplorer);
  } else {
    initSchemaExplorer();
  }
})();
