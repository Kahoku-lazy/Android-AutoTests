<script setup>
import { Button as AnimalButton, Card } from "animal-island-vue";
import { ElTag } from "element-plus";

const props = defineProps({
  item: { type: Object, required: true },
});

const emit = defineEmits(["edit", "delete"]);

function cardColor() {
  if (props.item.enabled) return "app-teal";
  return "brown";
}

function cardPattern() {
  if (props.item.enabled) return "app-teal";
  return "brown";
}

function stepCount() {
  try {
    const data = props.item.steps_data;
    if (Array.isArray(data)) return data.length;
  } catch (_) {}
  return 0;
}
</script>

<template>
  <Card
    :color="cardColor()"
    :pattern="cardPattern()"
    class="case-card"
    @click="$emit('edit', item)"
  >
    <div class="case-card__body">
      <div class="case-card__header">
        <span class="case-card__id">{{ item.id }}</span>
        <el-tag
          :type="item.enabled ? 'success' : 'info'"
          effect="dark"
          size="small"
          round
        >
          {{ item.enabled ? "启用" : "停用" }}
        </el-tag>
      </div>
      <h4 class="case-card__title">{{ item.title || "未命名用例" }}</h4>
      <div class="case-card__meta">
        <span v-if="item.category" class="meta-tag">{{ item.category }}</span>
        <span v-if="item.directory_name" class="meta-tag meta-tag--dir">{{
          item.directory_name
        }}</span>
        <span class="meta-tag meta-tag--steps">{{ stepCount() }} 步骤</span>
      </div>
    </div>
    <div class="case-card__actions" @click.stop>
      <AnimalButton size="small" type="primary" @click="$emit('edit', item)"
        >编辑</AnimalButton
      >
      <AnimalButton size="small" danger plain @click="$emit('delete', item)"
        >删除</AnimalButton
      >
    </div>
  </Card>
</template>

<style scoped>
.case-card {
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.case-card:hover {
  transform: translateY(-2px);
}

.case-card__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.case-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.case-card__id {
  font-family: "SF Mono", "Fira Code", Consolas, monospace;
  font-size: 11px;
  font-weight: 600;
  color: #9f927d;
  background: rgba(139, 115, 85, 0.06);
  padding: 2px 8px;
  border-radius: 6px;
}

.case-card__title {
  font-family: Nunito, "Noto Sans SC", sans-serif;
  font-weight: 700;
  font-size: 15px;
  color: #4a3a28;
  margin: 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.meta-tag {
  font-size: 11px;
  font-weight: 600;
  color: #8a7b66;
  background: rgba(139, 115, 85, 0.06);
  padding: 2px 8px;
  border-radius: 8px;
}

.meta-tag--dir {
  color: #11a89b;
  background: rgba(25, 200, 185, 0.08);
}

.meta-tag--steps {
  color: #9f927d;
}

.case-card__actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px dashed rgba(196, 184, 158, 0.4);
}
</style>
