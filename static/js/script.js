// Expansão/recolhimento dos submenus
document.querySelectorAll('.expandable').forEach(button => {
    button.addEventListener('click', () => {
        const submenu = button.nextElementSibling;
        if (submenu && submenu.classList.contains('sub-menu')) {
            submenu.classList.toggle('hidden');
        }
    });
});


// Ação ao clicar nos itens do menu
document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', (event) => {
        const action = item.getAttribute('data-action');

        if (action === 'refresh') {
            window.location.reload(); // Recarrega a página
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const buttonHeader = document.querySelector('#button-header'); // Botão de barras
    const newMenu = document.querySelector('.new-menu'); // Menu lateral

    // Alternar a exibição do menu ao clicar no botão
    buttonHeader.addEventListener('click', () => {
        console.log('Botão clicado!'); // Verifica se o botão foi clicado

        // Verificar se a classe 'hidden' está presente
        if (newMenu.classList.contains('new-menu-open')) {
            console.log('Exibindo o menu...');
            newMenu.classList.remove('new-menu-open'); // Remove 'hidden' para exibir o menu
        } else {
            console.log('Ocultando o menu...');
            newMenu.classList.add('new-menu-open'); // Adiciona 'hidden' para ocultar o menu
        }
    });

    // Fechar o menu ao clicar fora dele
    document.addEventListener('click', (event) => {
        // Verifica se o clique foi fora do menu e do botão
        if (!newMenu.contains(event.target) && event.target !== buttonHeader) {
            if (newMenu.classList.contains('new-menu-open')) {
                newMenu.classList.remove('new-menu-open');
            }
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('.sub-menu a');
    const contentSections = document.querySelectorAll('.content');

    links.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();

            const targetId = link.getAttribute('data-target');
            if (!targetId) return;

            // Esconde todas as seções
            contentSections.forEach(section => section.classList.add('hidden'));

            // Mostra a seção correspondente
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.classList.remove('hidden');
            }
        });
    });
});


// Alternar sub-menus no menu lateral
document.querySelectorAll('.expandable').forEach(button => {
    button.addEventListener('click', () => {
        const subMenu = button.nextElementSibling;
        subMenu.classList.toggle('visible');
    });
});

// Rolagem suave para links do menu lateral
document.querySelectorAll('.sidebar a').forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);

        window.scrollTo({
            top: targetElement.offsetTop - 80, // Considera o tamanho do header fixo
            behavior: 'smooth'
        });
    });
});


    // Mostra o botão ao rolar para baixo
    const backToTopButton = document.getElementById('backToTop');

    window.onscroll = function() {
        if (document.body.scrollTop > 200 || document.documentElement.scrollTop > 200) {
            backToTopButton.style.display = "block";
        } else {
            backToTopButton.style.display = "none";
        }
    };

    // Rola até o topo ao clicar no botão
    backToTopButton.onclick = function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };

