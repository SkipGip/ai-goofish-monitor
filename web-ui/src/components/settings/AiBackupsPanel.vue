<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { http } from '@/lib/http'
import type { AIBackupProfile } from '@/api/settings'
const props = defineProps<{ modelValue?: AIBackupProfile[]; disabled?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: AIBackupProfile[]] }>()
const profiles = computed(() => props.modelValue ?? [])
const testing = ref<string | null>(null)
const results = ref<Record<string, string>>({})
function add() {
  emit('update:modelValue', [...profiles.value, { id: crypto.randomUUID(), name: `备用 ${profiles.value.length + 1}`, base_url: '', model: '', api_key: '', proxy_url: '' }])
}
function remove(id: string) { emit('update:modelValue', profiles.value.filter(p => p.id !== id)) }
function move(index: number, step: number) {
  const copy = [...profiles.value]
  const target = index + step
  if (target < 0 || target >= copy.length) return
  const current = copy[index]!
  copy[index] = copy[target]!
  copy[target] = current
  emit('update:modelValue', copy)
}
async function test(profile: AIBackupProfile) {
  testing.value = profile.id
  try {
    const result = await http('/api/settings/ai/backups/test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(profile) })
    results.value[profile.id] = result.message
  } catch (error) { results.value[profile.id] = error instanceof Error ? error.message : '测试失败' }
  finally { testing.value = null }
}
</script>
<template>
  <section class="space-y-4 border-t pt-5">
    <div><h3 class="font-semibold">备用 AI 配置</h3><p class="mt-1 text-sm text-gray-500">上方为主配置。每条商品从主配置开始，连续失败 5 次后按下方顺序切换。任一配置成功后结束当前分析，下一条重新优先使用主配置。全部失败则记录失败，不无限重试。</p></div>
    <div v-for="(profile, index) in profiles" :key="profile.id" class="space-y-3 rounded-lg border p-4">
      <div class="flex flex-wrap items-center gap-2"><strong>备用 {{ index + 1 }}</strong><Button variant="outline" size="sm" :disabled="disabled || index === 0" @click="move(index, -1)">上移</Button><Button variant="outline" size="sm" :disabled="disabled || index === profiles.length - 1" @click="move(index, 1)">下移</Button><Button variant="outline" size="sm" :disabled="disabled" @click="remove(profile.id)">删除</Button></div>
      <div class="grid gap-3 sm:grid-cols-2">
        <div><Label>配置名称</Label><Input v-model="profile.name" :disabled="disabled" /></div>
        <div><Label>模型名称</Label><Input v-model="profile.model" :disabled="disabled" placeholder="填写该中转支持的模型 ID" /></div>
        <div><Label>API Base URL</Label><Input v-model="profile.base_url" :disabled="disabled" placeholder="https://example.com/v1" /></div>
        <div><Label>API Key</Label><Input v-model="profile.api_key" :disabled="disabled" type="password" autocomplete="new-password" :placeholder="profile.api_key_set ? '已配置，留空保持不变' : '填写该中转的 Key'" /></div>
        <div><Label>代理地址（可选）</Label><Input v-model="profile.proxy_url" :disabled="disabled" placeholder="http://127.0.0.1:7890" /></div>
      </div>
      <p class="text-xs text-gray-500">更换中转地址时需要重新填写 Key。测试连接不会保存配置。</p>
      <Button variant="outline" :disabled="disabled || testing !== null" @click="test(profile)">{{ testing === profile.id ? '测试中…' : '测试此备用' }}</Button>
      <p v-if="results[profile.id]" class="text-sm" role="status">{{ results[profile.id] }}</p>
    </div>
    <Button variant="outline" :disabled="disabled || profiles.length >= 10" @click="add">添加备用 AI</Button>
    <p class="text-xs text-gray-500">添加、删除或排序后，点击下方“保存 AI 设置”。正在运行的任务需重启以完整加载新配置。需要图片分析时，请选择支持图片的模型。</p>
  </section>
</template>
