<script>
	let { m, color = '#64748b', size = 'h-9 w-9', text = 'text-xs', rounded = 'rounded-full', extra = '' } = $props();
	let failed = $state(false);
	const initials = $derived(m.n.split(' ').map((s) => s[0]).slice(0, 2).join(''));
</script>

{#if m.img && !failed}
	<img
		src={m.img}
		alt=""
		loading="lazy"
		referrerpolicy="no-referrer"
		onerror={() => (failed = true)}
		class="{size} {rounded} {extra} flex-none object-cover object-top ring-2"
		style:--tw-ring-color={color}
	/>
{:else}
	<span class="{size} {rounded} {text} {extra} grid flex-none place-items-center font-bold text-white" style:background={color}>{initials}</span>
{/if}
