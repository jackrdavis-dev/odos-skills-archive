const pipelineContent = {
  text: {
    label: 'ODOS Text Studio',
    title: 'Adventure facts become durable stages.',
    copy: 'The active Codex model generates one stage at a time and saves it before continuing. A single human choice combines any Style, Quest, and Antagonist from the monthly options.',
    input: 'Title, month, tone, and theme constraints',
    output: 'Eight Markdown stages and a versioned handoff',
    gate: 'Choose three independent monthly options',
    state: 'progress.json + stage checkpoints'
  },
  packet: {
    label: 'ODOS v5.1 Stateful Packet Compiler',
    title: 'Approved text becomes a locked visual product.',
    copy: 'The compiler separates page composition from illustration style, calibrates four representative proofs, and then generates one traceable raster candidate at a time until every tier-mapped asset passes.',
    input: 'Completed text handoff + immutable visual references',
    output: 'PNG masters, maps, tokens, PDFs, and three tier ZIPs',
    gate: 'Approve character, action, Scene page, and map proofs',
    state: 'run state + four locks + asset status + hashes'
  },
  release: {
    label: 'ODOS Release',
    title: 'The oldest eligible packet reaches customers.',
    copy: 'Release validates the product as deeply as it publishes it: one shop listing with three independently delivered editions, followed by tier-correct Patreon fulfillment and a public announcement last.',
    input: 'Oldest unpublished Ready folder with 3 valid ZIPs',
    output: 'Verified shop product + four coordinated Patreon posts',
    gate: 'Explicit live authority or one authorized scheduled run',
    state: 'release ledger + verified remote IDs and URLs'
  },
  media: {
    label: 'ODOS Media v1',
    title: 'The newest packet becomes a month of stories.',
    copy: 'Media combines completed Text Studio facts with approved Premium visuals, then locks that source fingerprint into exactly twelve Instagram posts, three Patreon articles, and one DiceStory blog package.',
    input: 'Newest valid packet + matching completed text sources',
    output: '16 source-grounded editorial deliverables',
    gate: 'Approve the complete, exact campaign snapshot',
    state: 'campaign manifest + source fingerprint + QA records'
  }
};

const detailFields = {
  label: document.querySelector('#detail-label'),
  title: document.querySelector('#detail-title'),
  copy: document.querySelector('#detail-copy'),
  input: document.querySelector('#detail-input'),
  output: document.querySelector('#detail-output'),
  gate: document.querySelector('#detail-gate'),
  state: document.querySelector('#detail-state')
};

document.querySelectorAll('.pipeline-node').forEach((button) => {
  button.addEventListener('click', () => {
    const content = pipelineContent[button.dataset.skill];
    document.querySelectorAll('.pipeline-node').forEach((node) => {
      const active = node === button;
      node.classList.toggle('is-active', active);
      node.setAttribute('aria-pressed', String(active));
    });
    Object.entries(detailFields).forEach(([key, element]) => {
      element.textContent = content[key];
    });
  });
});

const filter = document.querySelector('#archive-filter');
const archiveCards = [...document.querySelectorAll('.archive-card')];
const archiveCount = document.querySelector('#archive-count');
const archiveEmpty = document.querySelector('#archive-empty');

filter.addEventListener('input', () => {
  const query = filter.value.trim().toLowerCase();
  let visible = 0;
  archiveCards.forEach((card) => {
    const matches = !query || `${card.dataset.search} ${card.textContent}`.toLowerCase().includes(query);
    card.hidden = !matches;
    if (matches) visible += 1;
  });
  archiveCount.textContent = `${visible} source ${visible === 1 ? 'group' : 'groups'}`;
  archiveEmpty.hidden = visible !== 0;
});

const navToggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('#site-nav');
navToggle.addEventListener('click', () => {
  const expanded = navToggle.getAttribute('aria-expanded') === 'true';
  navToggle.setAttribute('aria-expanded', String(!expanded));
  nav.classList.toggle('is-open', !expanded);
});

nav.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => {
    navToggle.setAttribute('aria-expanded', 'false');
    nav.classList.remove('is-open');
  });
});

