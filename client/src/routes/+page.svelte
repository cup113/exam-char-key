<script lang="ts">
	import Counter from './Counter.svelte';

	let q = $state('其');
	let result = $state([]);

	function query() {
		fetch(`/api/query?q=${encodeURIComponent(q)}`, {
			method: 'GET'
		})
			.then((res) => res.json())
			.then((data) => (result = data));
	}
</script>

<svelte:head>
	<title>Home</title>
	<meta name="description" content="Svelte demo app" />
</svelte:head>

<section>
	<h1>三百字钥</h1>

	<div class="my-2 text-center">
		<input
			type="text"
			bind:value={q}
			placeholder="输入一个汉字"
			class="w-60 rounded-lg border border-orange-800 py-1 text-center"
		/>
		<button onclick={query} class="rounded-lg border border-orange-800 px-2 py-1">查询</button>
	</div>

	<div class="grid grid-cols-2">
		{#each result as record}
			<div class="px-4 py-2 shadow">
				<div class="text-xl font-bold">{record.name_passage}</div>
				<div class="indent-8">
					<span>{record.context.slice(0, record.index_range[0])}</span><strong class="bg-orange-300"
						>{record.context.slice(record.index_range[0], record.index_range[1])}</strong
					><span>{record.context.slice(record.index_range[1])}</span>
				</div>
				<div class="indent-8 text-orange-600">
					[<strong>{record.context.slice(record.index_range[0], record.index_range[1])}</strong>] {record.core_detail}
				</div>
			</div>
		{/each}
	</div>
</section>

<style>
	h1 {
		width: 100%;
	}
</style>
