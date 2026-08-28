<?php
/**
 * Prueba del snippet fuera de WordPress: simula wp_head con la salida real de
 * distintos plugins de SEO y comprueba que queda una sola etiqueta de cada tipo
 * y que es la nuestra.
 */
define( 'ABSPATH', __DIR__ );

$GLOBALS['mic_is_target'] = true;
function is_singular() { return true; }
function is_page( $slug ) { return $GLOBALS['mic_is_target']; }
function esc_attr( $s ) { return htmlspecialchars( $s, ENT_QUOTES, 'UTF-8' ); }

$GLOBALS['hooks'] = array();
function add_action( $hook, $fn, $prio = 10 ) { $GLOBALS['hooks'][ $hook ][] = array( $prio, $fn ); }

require __DIR__ . '/mic-og-paquete-de-optimizacion.php';

// Cabeceras tal como las emiten los plugins reales (comillas dobles, simples,
// con y sin barra de cierre, en una sola línea o en varias).
$heads = array(
	'Yoast' => '<title>Algo</title>' . "\n"
		. '<meta name="description" content="vieja" />' . "\n"
		. '<meta property="og:locale" content="es_ES" />' . "\n"
		. '<meta property="og:type" content="article" />' . "\n"
		. '<meta property="og:title" content="Título viejo de Yoast" />' . "\n"
		. '<meta property="og:image" content="https://mashaincanada.com/wp-content/uploads/logo-generico.png" />' . "\n"
		. '<meta name="twitter:card" content="summary" />' . "\n"
		. '<link rel="canonical" href="https://mashaincanada.com/paquete-de-optimizacion/" />' . "\n",

	'Rank Math' => "<!-- Rank Math -->\n"
		. "<meta property='og:locale' content='es_ES'/>\n"
		. "<meta property='og:title' content='Viejo Rank Math'/>\n"
		. "<meta property='og:image' content='https://ejemplo.com/mala.jpg'/>\n"
		. "<meta name='twitter:image' content='https://ejemplo.com/mala.jpg'/>\n"
		. "<script>var a = 1;</script>\n",

	'AIOSEO (una sola línea)' =>
		'<meta property="og:title" content="X" /><meta property="og:image" content="Y" /><meta name="twitter:card" content="summary" /><link rel="icon" href="/f.ico" />',

	'Sin plugin de SEO' => "<title>Algo</title>\n<link rel=\"canonical\" href=\"x\" />\n",
);

$fail = 0;
foreach ( $heads as $name => $head ) {
	// Reproduce el orden real: prioridad 0 abre buffer, el plugin imprime, PHP_INT_MAX cierra.
	ob_start();
	mic_og_buffer_start();
	echo $head;
	mic_og_buffer_end();
	$out = ob_get_clean();

	$og_title  = preg_match_all( '#property="og:title"#', $out );
	$og_image  = preg_match_all( '#property="og:image"#', $out );
	$tw_card   = preg_match_all( '#name="twitter:card"#', $out );
	$viejas    = preg_match_all( '#(Título viejo|Viejo Rank Math|logo-generico|ejemplo\.com)#', $out );
	$canonical = substr_count( $out, 'rel="canonical"' ) + substr_count( $out, "rel='canonical'" );
	$titulo    = substr_count( $out, '<title>' );
	$script    = substr_count( $out, '<script>' );

	$ok = ( 1 === $og_title ) && ( 1 === $og_image ) && ( 1 === $tw_card ) && ( 0 === $viejas );
	// El contenido que no es og:/twitter: debe sobrevivir intacto.
	$conserva = ( false === strpos( $head, 'canonical' ) || $canonical >= 1 )
		&& ( false === strpos( $head, '<title>' ) || $titulo >= 1 )
		&& ( false === strpos( $head, '<script>' ) || $script >= 1 );

	printf(
		"%-26s og:title=%d og:image=%d twitter:card=%d viejas=%d conserva_resto=%s  %s\n",
		$name, $og_title, $og_image, $tw_card, $viejas,
		$conserva ? 'sí' : 'NO',
		( $ok && $conserva ) ? 'OK' : 'FALLA'
	);
	if ( ! ( $ok && $conserva ) ) {
		$fail++;
		echo "--- salida ---\n$out\n--------------\n";
	}
}

// La página que no es el objetivo no debe tocarse en absoluto.
$GLOBALS['mic_is_target'] = false;
ob_start();
mic_og_buffer_start();
echo '<meta property="og:title" content="Otra página" />';
mic_og_buffer_end();
$otra = ob_get_clean();
$intacta = ( '<meta property="og:title" content="Otra página" />' === $otra );
echo 'Otra página del sitio       intacta=' . ( $intacta ? 'sí  OK' : 'NO  FALLA' ) . "\n";
if ( ! $intacta ) { $fail++; }

echo $fail ? "\n$fail prueba(s) fallaron\n" : "\nTodas las pruebas pasaron\n";
exit( $fail ? 1 : 0 );
