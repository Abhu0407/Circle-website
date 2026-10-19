<!-- Two columns of SectionCards (one column below 900px), as on Profile. -->
<template>
  <div class="cards"><slot /></div>
</template>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

@media (max-width: 900px) {
  .cards {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 560px) {
  .cards {
    gap: 16px;
  }
}
</style>
