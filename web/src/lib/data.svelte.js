import { base } from '$app/paths';

export const NONE = 'Ingen uppgift';
export const POLITICAL = 'Politiska uppdrag';

const PALETTE = [
	'#f472b6', '#a78bfa', '#60a5fa', '#34d399', '#fbbf24', '#f87171', '#22d3ee', '#a3e635',
	'#fb923c', '#e879f9', '#818cf8', '#2dd4bf', '#facc15', '#c084fc', '#4ade80', '#38bdf8',
	'#fda4af', '#93c5fd', '#fcd34d', '#86efac', '#d8b4fe', '#5eead4'
];

class Store {
	data = $state(null);
	error = $state(null);
	/** Index för första och sista mandatperiod i urvalet. */
	range = $state([0, 0]);
	/** 'alla' = alla yrken räknas, 'huvud' = bara huvudyrket */
	mode = $state('huvud');
	parties = $state([]);
	theme = $state('dark');

	async load() {
		if (this.data) return;
		try {
			const res = await fetch(`${base}/data.json`);
			const d = await res.json();
			d.groupColor = Object.fromEntries(
				[...d.groups, NONE].map((g, i) => [g, g === NONE ? '#64748b' : PALETTE[i % PALETTE.length]])
			);
			d.partyMap = Object.fromEntries(d.parties.map((p) => [p.c, p]));
			d.byId = new Map(d.members.map((m) => [m.id, m]));
			this.range = [0, d.terms.length - 1];
			this.data = d;
		} catch (e) {
			this.error = String(e);
		}
	}

	get termLabel() {
		if (!this.data) return '';
		const [a, b] = this.range;
		const t = this.data.terms;
		return a === b ? `${t[a].s}–${t[a].e}` : `${t[a].s}–${t[b].e}`;
	}

	/** Mandatperioder för en ledamot som ligger inom aktuellt urval. */
	termsInRange(m) {
		const [a, b] = this.range;
		return m.t.filter(
			(t) => t.t >= a && t.t <= b && (this.parties.length === 0 || this.parties.includes(t.p))
		);
	}

	/** Ledamöter som satt någon gång inom urvalet. */
	get selected() {
		if (!this.data) return [];
		return this.data.members.filter((m) => this.termsInRange(m).length > 0);
	}
}

export const store = new Store();

/** Grupper som en ledamot räknas till, givet läge. */
export function groupsOf(m, mode) {
	if (!m.y.length) return [NONE];
	if (mode === 'huvud') return [m.h];
	return [...new Set(m.y.map((y) => y.g))];
}

export function countGroups(members, mode) {
	const c = new Map();
	for (const m of members) for (const g of groupsOf(m, mode)) c.set(g, (c.get(g) ?? 0) + 1);
	return [...c.entries()].sort((a, b) => b[1] - a[1]);
}

export function lastParty(m) {
	return m.t[m.t.length - 1]?.p;
}

export function termSpan(m, terms) {
	const first = terms[m.t[0].t];
	const last = terms[m.t[m.t.length - 1].t];
	return `${first.s}–${last.e}`;
}

export function wikiUrl(m) {
	return m.w ? `https://sv.wikipedia.org/wiki/${encodeURIComponent(m.w.replaceAll(' ', '_'))}` : null;
}

export function pct(n, total) {
	return total ? `${((100 * n) / total).toFixed(1).replace('.', ',')} %` : '–';
}
