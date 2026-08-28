<?php
/**
 * Plugin Name: MIC – Open Graph: Paquete de Optimización
 * Description: Publica los metadatos Open Graph y Twitter Card correctos en la página del Paquete de Optimización. No modifica el diseño ni el contenido visible de la página.
 * Version:     1.0.0
 * Author:      Masha in Canada
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Valores a publicar.
 *
 * MIC_OG_IMAGE: lo ideal es subir la imagen a Medios y pegar aquí la URL que
 * muestra la Biblioteca de Medios (queda bajo el dominio propio). La URL de
 * GitHub que viene por defecto funciona y sirve para arrancar el mismo día.
 */
const MIC_OG_SLUG  = 'paquete-de-optimizacion';
const MIC_OG_URL   = 'https://mashaincanada.com/paquete-de-optimizacion/';
const MIC_OG_TITLE = 'Paquete de Optimización | Tu camino a una oferta laboral en Canadá';
const MIC_OG_DESC  = 'Currículum, LinkedIn y estrategia de aplicación optimizados para el mercado canadiense. Destaca frente a empleadores y recruiters en Canadá con el acompañamiento de una Certified Résumé Strategist.';
const MIC_OG_IMAGE = 'https://raw.githubusercontent.com/mashaincanada-beep/masha-content-os-assets/main/assets/og/paquete-de-optimizacion-og.jpg';
const MIC_OG_ALT   = 'Paquete de Optimización de Masha in Canada: tu camino a una oferta laboral en Canadá empieza aquí.';

/**
 * ¿Estamos en la página del Paquete de Optimización?
 */
function mic_og_is_target_page() {
	return is_singular() && is_page( MIC_OG_SLUG );
}

/**
 * Las etiquetas que queremos publicar.
 */
function mic_og_tags() {
	$tags = array(
		array( 'property', 'og:type', 'website' ),
		array( 'property', 'og:site_name', 'Masha in Canada' ),
		array( 'property', 'og:locale', 'es_ES' ),
		array( 'property', 'og:url', MIC_OG_URL ),
		array( 'property', 'og:title', MIC_OG_TITLE ),
		array( 'property', 'og:description', MIC_OG_DESC ),
		array( 'property', 'og:image', MIC_OG_IMAGE ),
		array( 'property', 'og:image:secure_url', MIC_OG_IMAGE ),
		array( 'property', 'og:image:type', 'image/jpeg' ),
		array( 'property', 'og:image:width', '1200' ),
		array( 'property', 'og:image:height', '630' ),
		array( 'property', 'og:image:alt', MIC_OG_ALT ),
		array( 'name', 'twitter:card', 'summary_large_image' ),
		array( 'name', 'twitter:title', MIC_OG_TITLE ),
		array( 'name', 'twitter:description', MIC_OG_DESC ),
		array( 'name', 'twitter:image', MIC_OG_IMAGE ),
		array( 'name', 'twitter:image:alt', MIC_OG_ALT ),
	);

	$html = '';
	foreach ( $tags as $tag ) {
		$html .= sprintf(
			"<meta %s=\"%s\" content=\"%s\" />\n",
			$tag[0],
			esc_attr( $tag[1] ),
			esc_attr( $tag[2] )
		);
	}

	return $html;
}

/**
 * Quita las etiquetas og:/twitter: que ya haya emitido cualquier otro plugin.
 *
 * Se hace sobre el HTML del <head> y solo en esta página, para que no queden
 * etiquetas duplicadas (Meta se queda con la primera que encuentra, que sería
 * la del plugin de SEO y no la nuestra).
 */
function mic_og_strip_existing( $head_html ) {
	$pattern = '#<meta\b[^>]*?(?:property|name)\s*=\s*["\'](?:og:|twitter:)[^"\']*["\'][^>]*>[ \t]*\r?\n?#i';
	$clean   = preg_replace( $pattern, '', $head_html );

	// Si la expresión regular falla por lo que sea, devolvemos el head intacto.
	return ( null === $clean ) ? $head_html : $clean;
}

/**
 * Abre el buffer al principio del <head>.
 */
function mic_og_buffer_start() {
	if ( mic_og_is_target_page() ) {
		ob_start();
	}
}
add_action( 'wp_head', 'mic_og_buffer_start', 0 );

/**
 * Cierra el buffer al final del <head>, limpia y añade nuestras etiquetas.
 */
function mic_og_buffer_end() {
	if ( ! mic_og_is_target_page() ) {
		return;
	}

	$head_html = ob_get_clean();

	// ob_get_clean() devuelve false si no había buffer abierto: en ese caso no
	// hay nada que limpiar y solo añadimos nuestras etiquetas.
	if ( false === $head_html ) {
		echo mic_og_tags(); // phpcs:ignore WordPress.Security.EscapeOutput
		return;
	}

	echo mic_og_strip_existing( $head_html ); // phpcs:ignore WordPress.Security.EscapeOutput
	echo mic_og_tags(); // phpcs:ignore WordPress.Security.EscapeOutput
}
add_action( 'wp_head', 'mic_og_buffer_end', PHP_INT_MAX );
