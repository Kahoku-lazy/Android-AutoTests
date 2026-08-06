/** useHeroImage — 登录页视觉图加载状态。 */
import { ref, type Ref } from "vue"

export interface UseHeroImageReturn {
  heroImageSrc: string
  heroImageVisible: Ref<boolean>
  onHeroImageError: () => void
}

const HERO_IMAGE_SRC = "/login/login-hero.jpg"

export function useHeroImage(): UseHeroImageReturn {
  const heroImageVisible = ref(true)

  function onHeroImageError() {
    heroImageVisible.value = false
  }

  return {
    heroImageSrc: HERO_IMAGE_SRC,
    heroImageVisible,
    onHeroImageError,
  }
}
