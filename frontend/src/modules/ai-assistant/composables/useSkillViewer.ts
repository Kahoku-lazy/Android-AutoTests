/** useSkillViewer — 加载 skill 目录树与文件内容 */
import { ref, watch, type Ref } from 'vue'
import { fetchSharedSkillFile, fetchSharedSkillTree, type SkillFilePayload, type SkillTreeNode } from '../api/toolbox'
import { firstSkillFilePath } from '../helpers/skill-markdown'

export function useSkillViewer(skillName: Ref<string>) {
  const tree = ref<SkillTreeNode[]>([])
  const treeLoading = ref(false)
  const treeError = ref('')
  const selectedPath = ref('')
  const file = ref<SkillFilePayload | null>(null)
  const fileLoading = ref(false)
  const fileError = ref('')

  async function loadTree() {
    const name = skillName.value
    treeLoading.value = true
    treeError.value = ''
    tree.value = []
    selectedPath.value = ''
    file.value = null
    try {
      const data = await fetchSharedSkillTree(name)
      if (!data.status) {
        treeError.value = data.message || '无法加载 Skill 目录'
        return
      }
      tree.value = data.data?.tree || []
      const initial = firstSkillFilePath(tree.value)
      if (initial) await loadFile(initial)
    } catch {
      treeError.value = '无法加载 Skill 目录'
    } finally {
      treeLoading.value = false
    }
  }

  async function loadFile(path: string) {
    selectedPath.value = path
    fileLoading.value = true
    fileError.value = ''
    try {
      const data = await fetchSharedSkillFile(skillName.value, path)
      if (!data.status || !data.data) {
        fileError.value = data.message || '无法读取文件'
        file.value = null
        return
      }
      file.value = data.data
    } catch {
      fileError.value = '无法读取文件'
      file.value = null
    } finally {
      fileLoading.value = false
    }
  }

  watch(skillName, () => { void loadTree() }, { immediate: true })

  return {
    tree, treeLoading, treeError, selectedPath, file, fileLoading, fileError, loadTree, loadFile,
  }
}
