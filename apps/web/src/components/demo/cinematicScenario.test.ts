import { describe, expect, it } from 'vitest';
import {
  DEMO_PHASES,
  FINDINGS,
  GRAPH_EDGES,
  GRAPH_NODES,
  HYPOTHESES,
  MITRE_CELLS,
  QUERIES,
  REPORT_PAGES,
  TOTAL_SECONDS,
  getDemoState,
  runCinematicConsistencyChecks,
} from './cinematicScenario';

describe('cinematic Pix demo scenario', () => {
  it('passes ten deterministic end-to-end demo checks', () => {
    expect(runCinematicConsistencyChecks(10)).toEqual([]);
  });

  it('meets the CARD-013 timing gates', () => {
    const firstHypothesisAt = 11;
    const firstQueryAt = QUERIES[0].startsAt;
    const firstFindingAt = FINDINGS[0].appearsAt;
    const correlationAt = DEMO_PHASES.find((phase) => phase.id === 'correlation')?.startsAt ?? Infinity;
    const reportAt = DEMO_PHASES.find((phase) => phase.id === 'report')?.startsAt ?? Infinity;

    expect(firstHypothesisAt).toBeLessThan(15);
    expect(firstQueryAt - firstHypothesisAt).toBeLessThan(10);
    expect(firstFindingAt - firstQueryAt).toBeLessThan(30);
    expect(correlationAt - firstFindingAt).toBeLessThan(60);
    expect(reportAt - correlationAt).toBeLessThan(90);
    expect(TOTAL_SECONDS).toBeGreaterThanOrEqual(180);
    expect(TOTAL_SECONDS).toBeLessThanOrEqual(300);
  });

  it('reveals the full narrative by the end', () => {
    const finalState = getDemoState(TOTAL_SECONDS);

    expect(finalState.visibleHypotheses).toHaveLength(HYPOTHESES.length);
    expect(finalState.visibleFindings).toHaveLength(FINDINGS.length);
    expect(finalState.visibleGraphNodes).toHaveLength(GRAPH_NODES.length);
    expect(finalState.visibleGraphEdges).toHaveLength(GRAPH_EDGES.length);
    expect(finalState.visibleMitreCells).toHaveLength(MITRE_CELLS.length);
    expect(finalState.reportPages).toHaveLength(REPORT_PAGES.length);
    expect(finalState.reportPages.length).toBeGreaterThanOrEqual(8);
    expect(finalState.reportPages.length).toBeLessThanOrEqual(12);
  });
});
