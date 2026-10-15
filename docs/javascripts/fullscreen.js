(() => {
  function initMermaidFullscreen() {
    document.querySelectorAll('.mermaid').forEach((mermaidEl) => {
      if (mermaidEl.closest('.mermaid-container')) return;

      const container = document.createElement('div');
      container.className = 'mermaid-container';
      mermaidEl.parentNode.insertBefore(container, mermaidEl);
      container.appendChild(mermaidEl);

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'mermaid-fullscreen-btn';
      btn.setAttribute('aria-label', 'Toggle fullscreen');
      btn.innerHTML = '⛶ Fullscreen';
      btn.onclick = () => {
        if (!document.fullscreenElement) {
          if (container.requestFullscreen) {
            container.requestFullscreen();
          } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
          }
        } else {
          if (document.exitFullscreen) {
            document.exitFullscreen();
          }
        }
      };
      container.appendChild(btn);
    });
  }

  document.addEventListener('fullscreenchange', () => {
    const isFs = !!document.fullscreenElement;
    document.querySelectorAll('.mermaid-fullscreen-btn').forEach((btn) => {
      btn.innerHTML = isFs ? '✕ Exit' : '⛶ Fullscreen';
    });
  });

  // Interactive Diagram Linking to LinkML Schema Reference
  const KNOWN_CLASSES = new Set([
    'UrbanSimBlockMarginals', 'BlockToTazMapping', 'UrbanSimZonalTotals',
    'DemosPolarisMappedHousehold', 'DemosPolarisMappedPerson',
    'AtlasHouseholdFleetOutput', 'AtlasVehicleFleetOutput',
    'AtlasBodyTypeEnum', 'AtlasPowertrainEnum', 'AtlasVintageCategoryEnum',
    'PolarisDemandDatabaseHousehold', 'PolarisDemandDatabasePerson', 'PolarisDemandDatabaseVehicle',
    'PolarisTransitSkimsRecord', 'PolarisHighwaySkimsRecord', 'InputNetworkSkims', 'NextYearNetworkSkims',
    'ActivitySimHouseholdInputRecord', 'ActivitySimPersonInputRecord', 'ActivitySimLandUseZoneRecord',
    'BeamHouseholdRecord', 'BeamPersonRecord', 'BeamVehicleRecord',
    'BeamPlanRecord', 'BeamPlanOutputRecord', 'BeamNetworkSkims', 'BeamODSkimsRecord',
    'SynthFirmEstablishmentRecord', 'SynthFirmCarrierRecord',
    'SynthFirmB2BShipmentRecord', 'SynthFirmInternationalFreightRecord',
    'SynthFirmModeChoiceEnum', 'SynthFirmPowertrainEnum', 'SynthFirmPortTypeEnum'
  ]);

  function getSchemaUrl(className) {
    let base = '..';
    const configEl = document.getElementById('__config');
    if (configEl) {
      try {
        const config = JSON.parse(configEl.textContent);
        if (config.base !== undefined) base = config.base;
      } catch (e) {}
    }
    const prefix = base ? `${base}/` : '';
    return `${prefix}schema/${className}/`;
  }

  function initDiagramLinks() {
    document.querySelectorAll('.mermaid svg').forEach((svg) => {
      svg.querySelectorAll('g.node, g.classGroup, g[id^="entity-"], g[id^="classId-"]').forEach((group) => {
        if (group.dataset.linkmlBound) return;

        let matchedClass = null;
        const textElements = group.querySelectorAll('text, span');
        for (const t of textElements) {
          const raw = t.textContent.trim();
          const word = raw.split(/[\s<([{]/)[0];
          if (KNOWN_CLASSES.has(word)) {
            matchedClass = word;
            break;
          }
        }

        if (matchedClass) {
          group.dataset.linkmlBound = 'true';
          group.style.cursor = 'pointer';

          let titleEl = group.querySelector('title');
          if (!titleEl) {
            titleEl = document.createElementNS('http://www.w3.org/2000/svg', 'title');
            group.appendChild(titleEl);
          }
          titleEl.textContent = `View ${matchedClass} LinkML schema specification`;

          group.addEventListener('click', (e) => {
            if (e.target.closest('.mermaid-fullscreen-btn')) return;
            e.stopPropagation();
            window.location.href = getSchemaUrl(matchedClass);
          });
        }
      });
    });
  }

  function initAll() {
    initMermaidFullscreen();
    initDiagramLinks();
  }

  if (typeof document$ !== 'undefined') {
    document$.subscribe(initAll);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  setInterval(initAll, 500);
})();
