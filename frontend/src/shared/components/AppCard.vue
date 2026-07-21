<script setup>
defineProps({
  color: { type: String, default: '' },
  type: { type: String, default: 'default' },
})
</script>
<template>
  <el-card
    :class="['ac-card', color ? 'ac-card--' + color.replace('app-','') : '', type === 'dashed' ? 'ac-card--dashed' : '']"
    shadow="never"
  >
    <template v-for="(_, slot) in $slots" :key="slot" #[slot]>
      <slot :name="slot" />
    </template>
  </el-card>
</template>
