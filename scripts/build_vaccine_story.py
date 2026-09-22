"""A deliberately scripted, auditable vaccine-to-plasmablast demonstration.

Uses complete legal kernel rounds, with no Jev import or credential access.
The local antigen challenge and favorable neighboring clones are declared
initial conditions, not evidence of the frequency of this outcome.
"""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import Simulation, SCENARIOS, STATES


def build_story(cd40=True, hla_match=True):
    sim = Simulation(seed=21, scenario='baseline', initial_cells=100)
    sim.scenario = 'vaccine'
    sim.config = dict(SCENARIOS['vaccine'], cd40=cd40, hla_match=hla_match)
    # Existing adjacent cells in the initialized tissue; no moved cell centers.
    cast = dict(dc='LN-0018', helper='LN-0083', b='LN-0054')
    dc, helper, b = (sim.get(cast[k]) for k in ('dc','helper','b'))
    assert b['bcr'] == 'E1'
    sim.initial = sim.snapshot()
    sim.frames = []
    sim.save_frame()

    def full_frame():
        return dict(**sim.snapshot(), antigen_ledger=copy.deepcopy(sim.antigens))

    baseline = full_frame()
    sim.inject(2)
    # A local tissue perturbation near an already neighboring cognate trio.
    # The arrival animation is schematic; these are the sampled input positions.
    for antigen, cell, offset in zip(sim.antigens, (dc,b), ((-7,8),(8,3))):
        antigen.update(x=cell['x']+offset[0], y=cell['y']+offset[1])
    sim.inputs[-1]['placement'] = 'Proposed local antigen challenge: two finite native-antigen packets beside the selected DC and B cell.'
    sim.inputs[-1]['positions'] = [{k:a[k] for k in ('id','x','y')} for a in sim.antigens]
    sim.assert_invariants()
    frames = [full_frame()]
    for _ in range(20):
        rows = sim.proposals()
        answers = {}
        for row in rows:
            cid, options = row['id'], row['options']
            priority = (['CAPTURE','PROCESS'] if cid==dc['id'] else
                        ['PRIME','HELPER'] if cid==helper['id'] else
                        ['CAPTURE','PROCESS','HELP','PLASMA','SECRETE'] if cid==b['id'] else [])
            action = next((a for a in priority if a in options), 'WAIT')
            answers[cid] = dict(choice=action, probabilities={a:float(a==action) for a in options},
                                confidence=1, source='scripted')
        sim.step(answers, rows, source='scripted')
        frames.append(full_frame())
        if sim.antibody >= 3:
            break
    episode = sim.export()
    episode.update(provider_label='scripted', paid_requests=0,
                   recording_status='complete',
                   assumptions=episode['assumptions']+' Deliberately selected neighboring cognate trio and local antigen input; programmed plasmablast-favoring choices. Not an unbiased outcome estimate.')
    return dict(format='lymph-node-vaccine-story-v1', title='From vaccine antigen to antibody',
                provider='scripted', paid_requests=0, cast=cast, registry=sim.registry, states=STATES,
                baseline=baseline, frames=frames, episode=episode,
                presentation=dict(duration_seconds=76, arrival_seconds=8,
                    note='Playback time is compressed. Cell poses, arrival trails, presentation symbols and antibody icons are illustrative; transitions, contact eligibility, clocks and secretion counts come from the LN kernel.'),
                beats=[
                    dict(id='arrival', time=-1, end=0, title='Vaccine antigen arrives', short='Antigen',
                         cell=cast['dc'], action='LOCAL INPUT',
                         description='A local vaccine-antigen pulse perturbs the quiet tissue. Two finite packets of the same protein reach a dendritic cell and a cognate B cell.'),
                    dict(id='capture', time=0, end=30, title='The cells capture antigen', short='Uptake',
                         cell=cast['dc'], action='CAPTURE',
                         description='The dendritic cell takes antigen inside. The B cell independently captures native antigen through its matching BCR.'),
                    dict(id='process', time=30, end=120, title='Protein becomes a presented peptide', short='Present',
                         cell=cast['dc'], action='PROCESS → LOAD',
                         description='Internalized protein is processed, then loaded onto MHC II. Mint surface markers show the peptide–MHC complexes on the DC and B cell.'),
                    dict(id='prime', time=120, end=180, title='The dendritic cell primes CD4', short='Prime CD4',
                         cell=cast['helper'], action='PRIME',
                         description='A nearby CD4 T cell recognizes the DC’s compatible peptide–MHC II with costimulation. Their physical contact starts a timed priming program.'),
                    dict(id='helper', time=180, end=300, title='CD4 enters the follicular-helper pathway', short='Tfh pathway',
                         cell=cast['helper'], action='HELPER',
                         description='The activated CD4 cell becomes a Tfh precursor. Cognate B-cell interaction completes the helper state in this proposed model.'),
                    dict(id='help', time=300, end=330, title='The helper licenses this B cell', short='Help B',
                         cell=cast['b'], action='HELP',
                         description='The B cell presents the matching peptide to the CD4 helper. Local CD40-dependent help grants a finite differentiation license.'),
                    dict(id='commit', time=330, end=510, title='The B cell chooses the plasmablast route', short='Commit',
                         cell=cast['b'], action='PLASMA',
                         description='The scripted policy selects the eligible plasmablast program. The same B-cell identity and clone are preserved while differentiation takes time.'),
                    dict(id='secrete', time=510, end=600, title='The plasmablast releases antibody', short='Antibody',
                         cell=cast['b'], action='SECRETE',
                         description='The committed plasmablast secretes IgM of its original clone and antigen specificity. Each recorded secretion adds one arbitrary output unit.'),
                ],
                sources=[dict(title='Goenka et al. · DC presentation initiates the Tfh program', url='https://doi.org/10.4049/jimmunol.1100853')])


if __name__ == '__main__':
    story = build_story()
    final = story['frames'][-1]
    assert final['metrics']['antibodies'] == 3
    assert final['metrics']['states']['plasmablast'] == 1
    assert final['metrics']['tfh'] == 1
    path = ROOT / 'web/vaccine-story.json'
    path.write_text(json.dumps(story, ensure_ascii=True, separators=(',',':')), encoding='utf-8')
    print(json.dumps(dict(rounds=final['round'], time_min=final['time_min'],
                         scripted_decisions=final['metrics']['decisions'],
                         plasmablasts=1, antibody_units=3, paid_requests=0)))
