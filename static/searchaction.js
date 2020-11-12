
// credit: https://stackoverflow.com/a/50388154/6376756
function actionReddit(){
	var action_src = $("#uReddit").val();
	var urlLink = "/reddit/";
	var found = action_src.match(/(?:^|\/u\/|https:\/\/(?:www\.)?reddit\.com\/u(?:ser)?\/)([A-Za-z0-9_-]+)(?:\/)?$/i);
	if (!found) {
	    urlLink = "/error/?search=reddit&reason=invalid-username&data="+encodeURIComponent(action_src);
    } else {
        urlLink = urlLink + found[1];
    }
    window.location = urlLink;
	return false;
}

function actionTwitter(){
	var action_src = $("#uTwitter").val();
	var urlLink = "/twitter/";
	var found = action_src.match(/^(?:https:\/\/twitter\.com\/)?(?:#!\/)?(?:@)?([A-Za-z0-9_]{4,15})(?:\/)?$/i);
	if (!found) {
	    urlLink = "/error/?search=twitter&reason=invalid-username&data="+encodeURIComponent(action_src);
	} else {
	    urlLink = urlLink + found[1];
	}
	window.location = urlLink;
	return false;
}
